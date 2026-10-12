# Vast S8 m_hi resume: two-stage 16-bit merge, then fetch to this PC.
# Cursor may run this with no -Go (readiness only: no vastai, no SSH, no rent).
# Grok Bot runs -Go after operator go: rent one GPU, merge, scp the merged folder
# to fine_tuning/models, destroy. Do not upload to Hugging Face from this script
# or from the pod. Hub upload is a later local step after Cursor checks the copy.
# Do NOT call vast_cpt_s8_mhi_resume_orchestrate.ps1 -Go (that trains from ckpt-800).
param(
    [switch]$Go,
    [string]$OfferId = "",
    [switch]$KeepInstance,
    [int]$DiskGb = 80,
    [switch]$No3090Fallback
)

$ErrorActionPreference = "Stop"

$CptRootLocal = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$RepoRootLocal = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

$ExpectedSha = "2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207"
$MergeParentSha = "a70fded8aea1c9cb1a484e640e89137412519c28d95bdbfbf8d73ca2d2e42eac"
$PhaseASha = "06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432"
$AdapterDir = Join-Path $CptRootLocal "kaggle\runpod_cpt_v3\vast_cpt_s8_mhi_resume\fetch\mhi_resume\theology_cpt_lora"
$MergeParentDir = Join-Path $CptRootLocal "kaggle\runpod_cpt_v3\vast_cpt_s7_p0\fetch\theology_cpt_lora_s5best"
$FtScriptsLocal = Join-Path $RepoRootLocal "fine_tuning\scripts"
$MergePy = Join-Path $FtScriptsLocal "merge_cpt_lora.py"
$TwoStagePy = Join-Path $FtScriptsLocal "merge_cpt_s8_mhi_resume.py"
$ReadyPy = Join-Path $FtScriptsLocal "cpt_s8_mhi_resume_merge_readiness.py"
$RemoteSh = Join-Path $FtScriptsLocal "cpt_remote_merge_s8_mhi_resume.sh"
$ModelsDir = Join-Path $RepoRootLocal "fine_tuning\models"
$LocalMerged = Join-Path $ModelsDir "qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit"
$ResultsDir = Join-Path $CptRootLocal "kaggle\runpod_cpt_v3\vast_cpt_s8_mhi_resume_hf_export"
$RemoteMerged = "/workspace/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit"

Write-Host "=== Vast S8 m_hi resume HF export (merge + fetch, no Hub upload) ==="
Write-Host "go=$Go disk=${DiskGb}GB expected_sha=$ExpectedSha"
Write-Host "stack=Unsloth 2026.8.22 + torch 2.8.0+cu126"
Write-Host "adapter=$AdapterDir"
Write-Host "merge_parent=$MergeParentDir"
Write-Host "local_merged=$LocalMerged"
Write-Host "results=$ResultsDir"

$py = Join-Path $RepoRootLocal ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
& $py $ReadyPy
if ($LASTEXITCODE -ne 0) { throw "merge readiness FAIL" }

if (-not (Test-Path $ModelsDir)) { New-Item -ItemType Directory -Force -Path $ModelsDir | Out-Null }
$driveRoot = [System.IO.Path]::GetPathRoot((Resolve-Path $ModelsDir).Path)
$free = ([System.IO.DriveInfo]::new($driveRoot.TrimEnd('\'))).AvailableFreeSpace
Write-Host ("fetch_disk_free_gb={0:N1} need_gb=30" -f ($free / 1GB))
if ($free -lt 30GB) {
    throw "Need >=30 GB free under $ModelsDir to fetch the merged 16-bit model."
}

if (-not $Go) {
    Write-Host ""
    Write-Host "DRY COMPLETE -- readiness only. No GPU rent. No Hugging Face upload."
    Write-Host "Local merged folder is fetched by Grok Bot -Go, then checked with:"
    Write-Host "  python fine_tuning\scripts\cpt_s8_mhi_resume_merge_readiness.py --check-local"
    Write-Host "Grok Bot runs this only after Rafael says go:"
    Write-Host "  cd continued_pretrain\scripts"
    Write-Host "  .\vast_cpt_s8_mhi_resume_hf_export_orchestrate.ps1 -Go"
    exit 0
}

# --- -Go only: one GPU, fetch merged HF, destroy on success ---
$env:VAST_SESSION_FILE = Join-Path $CptRootLocal "kaggle\runpod_cpt_v3\vast_cpt_s8_mhi_resume_hf_export_session.json"
$env:VAST_LOCAL_RESULTS_DIR = $ResultsDir

. "$PSScriptRoot\vast_cpt_common.ps1"

$FtScripts = Join-Path $RepoRoot "fine_tuning\scripts"
$Script:DefaultLabel = "cpt-s8-mhi-merge-hf"
$Script:DefaultDiskGb = $DiskGb
$Script:MaxWallHours = 2
$Script:SearchQuery = "num_gpus=1 gpu_name=RTX_4090 reliability>=0.90 disk_space>=60 gpu_frac>=1 cuda_max_good>=12.6"
$Script:SearchQuery3090 = "num_gpus=1 gpu_name=RTX_3090 reliability>=0.90 disk_space>=60 gpu_frac>=1 cuda_max_good>=12.6"

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null

function Invoke-MergeSsh([string]$Remote) {
    $session = Get-VastSession
    if (-not $session -or -not $session.ssh_host) { throw "No SSH session for merge export" }
    $sshArgs = (Get-VastSshArgs $session) + @((Get-VastSshRemote $session), $Remote)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & ssh @sshArgs
        $Script:LastRemoteExit = [int]$LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $prev
    }
}

function Send-ToWorkspace([string]$Local, [string]$Remote) {
    $session = Get-VastSession
    $port = Get-VastSshPort $session
    $target = Get-VastSshRemote $session
    $scpBase = @("-i", $SshKey, "-P", "$port", "-o", "StrictHostKeyChecking=accept-new")
    Write-Host "scp $Local -> ${target}:$Remote"
    & scp @($scpBase + @("-r", $Local, "${target}:$Remote"))
    if ($LASTEXITCODE -ne 0) { throw "scp failed: $Local" }
}

foreach ($p in @($AdapterDir, $MergeParentDir, $MergePy, $TwoStagePy, $ReadyPy, $RemoteSh)) {
    if (-not (Test-Path $p)) { throw "Missing artifact: $p" }
}
$weights = Join-Path $AdapterDir "adapter_model.safetensors"
$gotSha = (Get-FileHash -Algorithm SHA256 -Path $weights).Hash.ToLower()
if ($gotSha -eq $PhaseASha) { throw "Refusing Phase A 06354dfc for this merge" }
if ($gotSha -ne $ExpectedSha) { throw "Local adapter SHA mismatch want=$ExpectedSha got=$gotSha" }
Write-Host "Local adapter SHA OK"
$mergeWeights = Join-Path $MergeParentDir "adapter_model.safetensors"
if (-not (Test-Path $mergeWeights)) { throw "Missing merge parent weights: $mergeWeights" }
$gotMergeSha = (Get-FileHash -Algorithm SHA256 -Path $mergeWeights).Hash.ToLower()
if ($gotMergeSha -ne $MergeParentSha) {
    throw "Local merge parent SHA mismatch want=$MergeParentSha got=$gotMergeSha"
}
Write-Host "Local merge parent a70 SHA OK"

Show-VastAccountSummary
$user = Invoke-VastaiJson -CliArgs @("show", "user")
$credit = [double]$user.credit
if ($credit -lt 2.0) {
    throw "Vast credit=$credit too low for merge export (need ~`$2+)"
}

$instText = Invoke-Vastai -CliArgs @("show", "instances") -RawJson
if ($instText -notmatch '^\s*\[\s*\]\s*$') {
    throw "Leftover Vast instances present - destroy before merge-export rent"
}

function Test-VastMergeGeoOk([string]$Geo) {
    if (-not $Geo) { return $false }
    $g = $Geo.ToLowerInvariant()
    foreach ($bad in @("thailand", "taiwan", "india", "vietnam", "indonesia", "china", "tw,", " th", ", th", " in,", ", in")) {
        if ($g.Contains($bad.Trim())) { return $false }
    }
    foreach ($good in @("hungary", "netherlands", "germany", "france", "poland", "czech", "romania", "sweden", "finland", "united states", "usa", "canada", "uk,", "united kingdom", "portugal", "spain", "italy", "belgium", "austria", "norway", "ireland", "iceland", "bulgaria", "slovakia", "slovenia", "estonia", "latvia", "lithuania")) {
        if ($g.Contains($good)) { return $true }
    }
    return $true
}

if (-not $OfferId) {
    $offers = @()
    try {
        $offers = @(Find-VastCheapestOffer -Query $SearchQuery -Limit 15)
    }
    catch {
        Write-Host "4090 search failed: $($_.Exception.Message)"
    }
    $pick = $null
    $fallback = $null
    foreach ($o in $offers) {
        $dphCand = if ($o.dph_total) { [double]$o.dph_total } else { [double]$o.dph }
        if ($dphCand -le 0 -or $dphCand -ge 1.2) { continue }
        $geo = [string]$o.geolocation
        if (-not $fallback) { $fallback = $o }
        if (Test-VastMergeGeoOk $geo) { $pick = $o; break }
        Write-Host "Skip slow/risky geo=$geo offer=$($o.id)"
    }
    if (-not $pick) { $pick = $fallback }

    if (-not $pick -and -not $No3090Fallback) {
        Write-Host "Falling back to RTX 3090 search ..."
        $offers = @(Find-VastCheapestOffer -Query $SearchQuery3090 -Limit 15)
        foreach ($o in $offers) {
            $dphCand = if ($o.dph_total) { [double]$o.dph_total } else { [double]$o.dph }
            if ($dphCand -le 0 -or $dphCand -ge 0.8) { continue }
            if (Test-VastMergeGeoOk ([string]$o.geolocation)) { $pick = $o; break }
        }
        if (-not $pick -and $offers.Count -gt 0) { $pick = $offers[0] }
    }

    if (-not $pick) {
        throw "No suitable Vast offer (pass -OfferId or check marketplace)"
    }
    $OfferId = [string]$pick.id
    if (-not $OfferId) { $OfferId = [string]$pick.ask_contract_id }
    $dph = if ($pick.dph_total) { $pick.dph_total } else { $pick.dph }
    Write-Host "Selected offer_id=$OfferId dph=$dph/hr gpu=$($pick.gpu_name) geo=$($pick.geolocation)"
}

Write-Host "Renting offer=$OfferId label=$DefaultLabel ..."
& (Join-Path $FtScripts "vast_provision.ps1") -OfferId $OfferId -DiskGb $DiskGb -Label $DefaultLabel -Force
if ($LASTEXITCODE -ne 0) { throw "provision failed" }

$session = Get-VastSession
$ht = Convert-SessionToHashtable $session
$ht.name = $DefaultLabel
$ht.max_wall_hours = $MaxWallHours
$ht.merge_export_adapter_sha = $ExpectedSha
$ht.merge_export_status = "provisioned"
Save-VastSession $ht

& (Join-Path $FtScripts "vast_wait_ssh.ps1")
if ($LASTEXITCODE -ne 0) { throw "wait_ssh failed" }
& (Join-Path $FtScripts "vast_verify_gpu.ps1")
if ($LASTEXITCODE -ne 0) { throw "verify_gpu failed" }

& (Join-Path $FtScripts "vast_inject_hf_token.ps1")
if ($LASTEXITCODE -ne 0) { throw "HF inject failed - merge needs the base-model download" }

Write-Host "Syncing merge assets (parent a70 + resume 22698039). No train mix. No Hub upload script."
Invoke-MergeSsh "mkdir -p /workspace/hf_home && rm -rf /workspace/theology_cpt_lora /workspace/merge_parent_a70 /workspace/theology_cpt_merged_a70 /workspace/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit"
Send-ToWorkspace $AdapterDir "/workspace/"
Invoke-MergeSsh 'if [[ -f /workspace/theology_cpt_lora/adapter_model.safetensors ]]; then echo LORA_LAYOUT_OK; elif [[ -f /workspace/theology_cpt_lora/theology_cpt_lora/adapter_model.safetensors ]]; then mv /workspace/theology_cpt_lora/theology_cpt_lora/* /workspace/theology_cpt_lora/ && rmdir /workspace/theology_cpt_lora/theology_cpt_lora 2>/dev/null; echo LORA_LAYOUT_FLATTENED; else echo LORA_LAYOUT_FAIL; ls -laR /workspace/theology_cpt_lora 2>/dev/null || true; exit 2; fi'
Invoke-MergeSsh "rm -rf /workspace/merge_parent_a70 && mkdir -p /workspace/merge_parent_a70"
Send-ToWorkspace $MergeParentDir "/workspace/merge_parent_a70"
Invoke-MergeSsh 'if [[ -f /workspace/merge_parent_a70/adapter_model.safetensors ]]; then echo MERGE_PARENT_LAYOUT_OK; elif [[ -f /workspace/merge_parent_a70/theology_cpt_lora_s5best/adapter_model.safetensors ]]; then mv /workspace/merge_parent_a70/theology_cpt_lora_s5best/* /workspace/merge_parent_a70/ && rmdir /workspace/merge_parent_a70/theology_cpt_lora_s5best 2>/dev/null; echo MERGE_PARENT_LAYOUT_FLATTENED; else echo MERGE_PARENT_LAYOUT_FAIL; ls -laR /workspace/merge_parent_a70 2>/dev/null || true; exit 2; fi'
Send-ToWorkspace $MergePy "/workspace/merge_cpt_lora.py"
Send-ToWorkspace $TwoStagePy "/workspace/merge_cpt_s8_mhi_resume.py"
Send-ToWorkspace $ReadyPy "/workspace/cpt_s8_mhi_resume_merge_readiness.py"
Send-ToWorkspace $RemoteSh "/workspace/cpt_remote_merge_s8_mhi_resume.sh"
Invoke-MergeSsh "sed -i 's/\r$//' /workspace/cpt_remote_merge_s8_mhi_resume.sh /workspace/merge_cpt_s8_mhi_resume.py /workspace/cpt_s8_mhi_resume_merge_readiness.py && chmod +x /workspace/cpt_remote_merge_s8_mhi_resume.sh && test -f /workspace/theology_cpt_lora/adapter_model.safetensors && test -f /workspace/merge_parent_a70/adapter_model.safetensors && test -f /workspace/merge_cpt_lora.py && test -f /workspace/merge_cpt_s8_mhi_resume.py && echo REMOTE_LAYOUT_OK"
if ($Script:LastRemoteExit -ne 0) { throw "remote layout check failed" }

$ht = Convert-SessionToHashtable (Get-VastSession)
$ht.merge_export_status = "running"
Save-VastSession $ht

Write-Host "Launching two-stage merge nohup (poll up to 2h). Pod does not upload to Hub."
Invoke-MergeSsh "rm -f /workspace/merge_s8.log /workspace/merge_s8_done.txt /workspace/merge_s8_rc.txt /workspace/merge_s8_launcher.log; nohup bash -lc 'bash /workspace/cpt_remote_merge_s8_mhi_resume.sh > /workspace/merge_s8.log 2>&1; echo `$? > /workspace/merge_s8_rc.txt; date -u > /workspace/merge_s8_done.txt' > /workspace/merge_s8_launcher.log 2>&1 & echo LAUNCHED"

$deadline = (Get-Date).AddHours(2)
$rc = -1
$done = $false
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 60
    $session = Get-VastSession
    if (-not $session.ssh_host) { Write-Host "poll: SSH lost"; break }
    $sshArgs = (Get-VastSshArgs $session) + @(
        (Get-VastSshRemote $session),
        "if [[ -f /workspace/merge_s8_done.txt ]]; then echo MERGE_DONE; cat /workspace/merge_s8_rc.txt; grep -E 'CPT_S8_MHI_RESUME_MERGE_DONE|PIN_OK|FAIL' /workspace/merge_s8.log | tail -n 5; elif pgrep -f cpt_remote_merge_s8_mhi_resume.sh >/dev/null || pgrep -f merge_cpt_s8_mhi_resume.py >/dev/null; then echo MERGE_RUNNING; tail -n 2 /workspace/merge_s8.log 2>/dev/null || tail -n 2 /workspace/merge_s8_launcher.log 2>/dev/null || true; else echo MERGE_IDLE; tail -n 5 /workspace/merge_s8_launcher.log 2>/dev/null || true; fi"
    )
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $pollOut = (& ssh @sshArgs 2>$null | Out-String)
    }
    catch {
        $pollOut = "poll_ssh_error"
    }
    finally {
        $ErrorActionPreference = $prev
    }
    $flat = ($pollOut -replace "`r|`n", " ").Trim()
    if ($flat.Length -gt 240) { $flat = $flat.Substring(0, 240) }
    Write-Host ("poll: " + $flat)
    if ($pollOut -match "MERGE_DONE") {
        $done = $true
        foreach ($ln in ($pollOut -split "`n")) {
            $t = $ln.Trim()
            if ($t -match '^\d+$') { $rc = [int]$t; break }
        }
        break
    }
}
if (-not $done) {
    Write-Host "WARN: poll deadline reached or SSH lost without merge_s8_done.txt"
    if ($rc -lt 0) { $rc = 124 }
}
Write-Host "remote exit=$rc"

$session = Get-VastSession
$port = Get-VastSshPort $session
$target = Get-VastSshRemote $session
$scpBase = @("-i", $SshKey, "-P", "$port", "-o", "StrictHostKeyChecking=accept-new")
$prevErr = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& scp @($scpBase + @("${target}:/workspace/merge_s8.log", (Join-Path $ResultsDir "merge_s8.log"))) 2>$null
& scp @($scpBase + @("${target}:/workspace/merge_s8_launcher.log", (Join-Path $ResultsDir "merge_s8_launcher.log"))) 2>$null
& scp @($scpBase + @("${target}:/workspace/merge_s8_rc.txt", (Join-Path $ResultsDir "merge_s8_rc.txt"))) 2>$null
$ErrorActionPreference = $prevErr

$remoteReady = $false
if ($rc -eq 0) {
    Invoke-MergeSsh "test -f $RemoteMerged/config.json && echo REMOTE_MERGED_OK"
    $remoteReady = ($Script:LastRemoteExit -eq 0)
}

$fetched = $false
if ($remoteReady) {
    Write-Host "Fetching merged 16-bit HF to $LocalMerged"
    if (Test-Path $LocalMerged) { Remove-Item -Recurse -Force $LocalMerged }
    & scp @($scpBase + @("-r", "${target}:${RemoteMerged}", $ModelsDir))
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FETCH FAIL: scp of merged weights failed. Keeping the instance."
    }
    else {
        & $py $ReadyPy --check-local --merged-path $LocalMerged
        $fetched = ($LASTEXITCODE -eq 0)
    }
}
else {
    Write-Host "Remote merge did not produce $RemoteMerged/config.json (rc=$rc). Keeping the instance."
}

$stamp = Get-Date -Format o
@"
remote_exit=$rc
adapter_sha=$ExpectedSha
merge_parent_sha=$MergeParentSha
local_merged=$LocalMerged
local_check_ok=$fetched
fetched=$stamp
unsloth=unsloth[colab-new]==2026.8.22
torch=2.8.0+cu126
hub_until_win=06354dfc
note=S8 m_hi resume two-stage 16-bit merge. Fetch before destroy. Do not upload from the pod. Do not overwrite LoRA v2.
"@ | Set-Content (Join-Path $ResultsDir "result.txt")
Write-Host "Merge logs -> $ResultsDir"

$ht = Convert-SessionToHashtable (Get-VastSession)
$ht.merge_export_status = if ($fetched) { "fetched" } else { "failed" }
$ht.merge_export_remote_exit = $rc
$ht.merge_export_fetched_at = $stamp
Save-VastSession $ht

if (-not $KeepInstance) {
    if (-not $fetched) {
        Write-Host "KEEPING instance after FAIL so merge_s8.log can be inspected."
        Write-Host "HINT: scp merge_s8.log then .\fine_tuning\scripts\vast_destroy.ps1"
    }
    else {
        Write-Host "Destroying Vast instance after local merged copy verified ..."
        & (Join-Path $FtScripts "vast_destroy.ps1")
    }
}

if ($fetched) {
    Write-Host "RESULT: MERGE FETCH COMPLETE - $LocalMerged"
    Write-Host "Cursor checks the folder next (--check-local). Grok Bot uploads only after that passes."
    Write-Host "Do not overwrite rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2."
    exit 0
}
Write-Host "RESULT: MERGE EXPORT FAIL rc=$rc local_ok=$fetched"
exit 1
