# Rent a Vast 4090, run Unsloth CPT+LoRA smoke (~3 train steps), fetch log, destroy.
param(
    [string]$OfferId = "",
    [switch]$KeepInstance,
    [int]$DiskGb = 50
)

$ErrorActionPreference = "Stop"
$FtScripts = (Resolve-Path (Join-Path $PSScriptRoot "..\..\fine_tuning\scripts")).Path
. (Join-Path $FtScripts "vast_common.ps1")

# Isolate from SFT session state; provision/wait/destroy still use their StateFile.
$CptRoot = Join-Path $RepoRoot "continued_pretrain"
$Script:StateFile = Join-Path $CptRoot "kaggle\runpod_cpt_v3\vast_cpt_smoke_session.json"
$Script:LocalResultsDir = Join-Path $CptRoot "kaggle\runpod_cpt_v3\vast_cpt_smoke"
$Script:DefaultLabel = "cpt-unsloth-smoke"
$Script:DefaultDiskGb = $DiskGb
$Script:SearchQuery = "num_gpus=1 gpu_name=RTX_4090 reliability>=0.90 disk_space>=40 gpu_frac>=1 cuda_max_good>=12.6"
$Script:MaxWallHours = 2
$sftSessionPath = Join-Path $FtRoot "kaggle\vast_sft_session.json"

New-Item -ItemType Directory -Force -Path $LocalResultsDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $StateFile -Parent) | Out-Null

function Invoke-SmokeSsh {
    param([string]$Remote)
    $session = Get-VastSession
    if (-not $session -or -not $session.ssh_host) {
        throw "No SSH session for smoke"
    }
    $sshArgs = (Get-VastSshArgs $session) + @((Get-VastSshRemote $session), $Remote)
    # Do not merge stderr (Vast banner) under ErrorAction=Stop; capture exit via script var.
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & ssh @sshArgs
        $Script:LastSmokeExit = [int]$LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $prev
    }
}

Write-Host "=== Vast Unsloth CPT+LoRA smoke (nvidia/cuda + unset LD_LIBRARY_PATH) ==="
Write-Host "Target disk=${DiskGb}GB label=$DefaultLabel image=nvidia/cuda mitigation=LD_LIBRARY_PATH"

if (-not $OfferId) {
    # Do NOT pass -d (verified-only); marketplace ~$0.47 is fine for smoke.
    $offers = Invoke-VastaiJson -CliArgs @(
        "search", "offers", $SearchQuery,
        "-o", "dph_total",
        "--limit", "8"
    )
    $list = @($offers)
    if ($list.Count -eq 0) {
        throw "No Vast offers matched smoke query"
    }
    $pick = $null
    foreach ($o in $list) {
        if ($o.dph_total) {
            $dphCand = [double]$o.dph_total
        }
        else {
            $dphCand = [double]$o.dph
        }
        if ($dphCand -gt 0 -and $dphCand -lt 1.0) {
            $pick = $o
            break
        }
    }
    if (-not $pick) {
        $pick = $list[0]
    }
    $OfferId = [string]$pick.id
    if (-not $OfferId) {
        $OfferId = [string]$pick.ask_contract_id
    }
    if ($pick.dph_total) {
        $dph = $pick.dph_total
    }
    else {
        $dph = $pick.dph
    }
    Write-Host "Selected offer_id=$OfferId dph=$dph/hr geo=$($pick.geolocation)"
}

Write-Host "Renting (billable) offer=$OfferId ~ expect setup+smoke under 1h ..."
& (Join-Path $FtScripts "vast_provision.ps1") -OfferId $OfferId -DiskGb $DiskGb -Label $DefaultLabel -Force
if ($LASTEXITCODE -ne 0) {
    throw "provision failed"
}

if (Test-Path $sftSessionPath) {
    $raw = Get-Content $sftSessionPath -Raw -Encoding utf8 | ConvertFrom-Json
    $ht = Convert-SessionToHashtable $raw
    $ht.name = $DefaultLabel
    $ht.max_wall_hours = $MaxWallHours
    Save-VastSession $ht
}

& (Join-Path $FtScripts "vast_wait_ssh.ps1")
if ($LASTEXITCODE -ne 0) {
    throw "wait_ssh failed"
}
& (Join-Path $FtScripts "vast_verify_gpu.ps1")
if ($LASTEXITCODE -ne 0) {
    throw "verify_gpu failed"
}

$session = Get-Content $sftSessionPath -Raw -Encoding utf8 | ConvertFrom-Json
Save-VastSession (Convert-SessionToHashtable $session)

& (Join-Path $FtScripts "vast_inject_hf_token.ps1")
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARN: HF inject failed - continuing (public base may still work)"
}

Write-Host "Syncing smoke scripts ..."
$scpBase = @("-i", $SshKey, "-P", "$(Get-VastSshPort $session)", "-o", "StrictHostKeyChecking=accept-new")
$target = Get-VastSshRemote $session
$smokePy = Join-Path $PSScriptRoot "smoke_vast_unsloth_cpt.py"
$smokeSh = Join-Path $PSScriptRoot "vast_cpt_smoke_remote.sh"
& scp @($scpBase + @($smokePy, "${target}:/workspace/smoke_vast_unsloth_cpt.py"))
if ($LASTEXITCODE -ne 0) {
    throw "scp smoke py failed"
}
& scp @($scpBase + @($smokeSh, "${target}:/workspace/vast_cpt_smoke_remote.sh"))
if ($LASTEXITCODE -ne 0) {
    throw "scp smoke sh failed"
}

Write-Host "Running remote smoke (setup + 3 Unsloth train steps) ..."
$Script:LastSmokeExit = -1
Invoke-SmokeSsh -Remote "chmod +x /workspace/vast_cpt_smoke_remote.sh; bash /workspace/vast_cpt_smoke_remote.sh"
$rc = $Script:LastSmokeExit
Write-Host "remote exit=$rc"

& scp @($scpBase + @("${target}:/workspace/cpt_unsloth_smoke.log", (Join-Path $LocalResultsDir "cpt_unsloth_smoke.log")))
$stamp = Get-Date -Format o
"remote_exit=$rc`nfetched=$stamp" | Set-Content (Join-Path $LocalResultsDir "result.txt")

$pass = $false
$logPath = Join-Path $LocalResultsDir "cpt_unsloth_smoke.log"
if (Test-Path $logPath) {
    $log = Get-Content $logPath -Raw
    if ($log -match "CPT_UNSLOTH_SMOKE_PASS") {
        $pass = $true
    }
    Write-Host "---- smoke log (tail) ----"
    Get-Content $logPath -Tail 40
}

if (-not $KeepInstance) {
    Write-Host "Destroying Vast instance (mandatory after smoke) ..."
    if (Test-Path $sftSessionPath) {
        & (Join-Path $FtScripts "vast_destroy.ps1")
    }
}

if ($pass) {
    Write-Host "RESULT: PASS - Vast + Unsloth CPT LoRA survived first train steps"
    exit 0
}
Write-Host "RESULT: FAIL - Unsloth CPT LoRA smoke did not pass (rc=$rc)"
exit 1
