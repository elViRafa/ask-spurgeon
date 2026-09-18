# Rent Vast 4090 (nvidia/cuda), run Unsloth CPT smoke inside Miniconda env, destroy.
param(
    [string]$OfferId = "",
    [switch]$KeepInstance,
    [int]$DiskGb = 60
)

$ErrorActionPreference = "Stop"
$FtScripts = (Resolve-Path (Join-Path $PSScriptRoot "..\..\fine_tuning\scripts")).Path
. (Join-Path $FtScripts "vast_common.ps1")

$CptRoot = Join-Path $RepoRoot "continued_pretrain"
$Script:StateFile = Join-Path $CptRoot "kaggle\runpod_cpt_v3\vast_cpt_smoke_session.json"
$Script:LocalResultsDir = Join-Path $CptRoot "kaggle\runpod_cpt_v3\vast_cpt_smoke"
$Script:DefaultLabel = "cpt-unsloth-conda-smoke"
$Script:DefaultDiskGb = $DiskGb
$Script:SearchQuery = "num_gpus=1 gpu_name=RTX_4090 reliability>=0.90 disk_space>=50 gpu_frac>=1 cuda_max_good>=12.6"
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

Write-Host "=== Vast Unsloth CPT+LoRA smoke (Miniconda env) ==="
Write-Host "disk=${DiskGb}GB label=$DefaultLabel (GitHub #668 conda workaround)"

if (-not $OfferId) {
    $offers = Invoke-VastaiJson -CliArgs @(
        "search", "offers", $SearchQuery,
        "-o", "dph_total",
        "--limit", "8"
    )
    $list = @($offers)
    if ($list.Count -eq 0) { throw "No Vast offers matched" }
    $pick = $null
    foreach ($o in $list) {
        if ($o.dph_total) { $dphCand = [double]$o.dph_total } else { $dphCand = [double]$o.dph }
        if ($dphCand -gt 0 -and $dphCand -lt 1.0) { $pick = $o; break }
    }
    if (-not $pick) { $pick = $list[0] }
    $OfferId = [string]$pick.id
    if (-not $OfferId) { $OfferId = [string]$pick.ask_contract_id }
    if ($pick.dph_total) { $dph = $pick.dph_total } else { $dph = $pick.dph }
    Write-Host "Selected offer_id=$OfferId dph=$dph/hr geo=$($pick.geolocation)"
}

Write-Host "Renting offer=$OfferId ..."
& (Join-Path $FtScripts "vast_provision.ps1") -OfferId $OfferId -DiskGb $DiskGb -Label $DefaultLabel -Force
if ($LASTEXITCODE -ne 0) { throw "provision failed" }

if (Test-Path $sftSessionPath) {
    $raw = Get-Content $sftSessionPath -Raw -Encoding utf8 | ConvertFrom-Json
    $ht = Convert-SessionToHashtable $raw
    $ht.name = $DefaultLabel
    $ht.max_wall_hours = $MaxWallHours
    Save-VastSession $ht
}

& (Join-Path $FtScripts "vast_wait_ssh.ps1")
if ($LASTEXITCODE -ne 0) { throw "wait_ssh failed" }
& (Join-Path $FtScripts "vast_verify_gpu.ps1")
if ($LASTEXITCODE -ne 0) { throw "verify_gpu failed" }

$session = Get-Content $sftSessionPath -Raw -Encoding utf8 | ConvertFrom-Json
Save-VastSession (Convert-SessionToHashtable $session)

& (Join-Path $FtScripts "vast_inject_hf_token.ps1")
if ($LASTEXITCODE -ne 0) { Write-Host "WARN: HF inject failed - continuing" }

Write-Host "Syncing smoke scripts ..."
$scpBase = @("-i", $SshKey, "-P", "$(Get-VastSshPort $session)", "-o", "StrictHostKeyChecking=accept-new")
$target = Get-VastSshRemote $session
$smokePy = Join-Path $PSScriptRoot "smoke_vast_unsloth_cpt.py"
$smokeSh = Join-Path $PSScriptRoot "vast_cpt_smoke_remote_conda.sh"
& scp @($scpBase + @($smokePy, "${target}:/workspace/smoke_vast_unsloth_cpt.py"))
if ($LASTEXITCODE -ne 0) { throw "scp py failed" }
& scp @($scpBase + @($smokeSh, "${target}:/workspace/vast_cpt_smoke_remote_conda.sh"))
if ($LASTEXITCODE -ne 0) { throw "scp sh failed" }

Write-Host "Running conda Unsloth smoke (setup may take 10-20m) ..."
$Script:LastSmokeExit = -1
Invoke-SmokeSsh -Remote "chmod +x /workspace/vast_cpt_smoke_remote_conda.sh; bash /workspace/vast_cpt_smoke_remote_conda.sh"
$rc = $Script:LastSmokeExit
Write-Host "remote exit=$rc"

& scp @($scpBase + @("${target}:/workspace/cpt_unsloth_smoke.log", (Join-Path $LocalResultsDir "cpt_unsloth_smoke_conda.log")))
$stamp = Get-Date -Format o
"remote_exit=$rc`nbackend=conda`nfetched=$stamp" | Set-Content (Join-Path $LocalResultsDir "result_conda.txt")

$pass = $false
$logPath = Join-Path $LocalResultsDir "cpt_unsloth_smoke_conda.log"
if (Test-Path $logPath) {
    $log = Get-Content $logPath -Raw
    if ($log -match "CPT_UNSLOTH_SMOKE_PASS") { $pass = $true }
    Write-Host "---- smoke log (tail) ----"
    Get-Content $logPath -Tail 50
}

if (-not $KeepInstance) {
    Write-Host "Destroying Vast instance ..."
    if (Test-Path $sftSessionPath) {
        & (Join-Path $FtScripts "vast_destroy.ps1")
    }
}

if ($pass) {
    Write-Host "RESULT: PASS - conda Unsloth CPT LoRA survived first train steps"
    exit 0
}
Write-Host "RESULT: FAIL - conda Unsloth CPT smoke did not pass (rc=$rc)"
exit 1
