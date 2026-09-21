# Vast S6 C-eval - score ckpt-2050 LoRA vs Ampere base (+ compare Hub v2 keep-bar offline).
# No training. No Hub overwrite. No merge. Destroys instance unless -KeepInstance.
param(
    [string]$OfferId = "",
    [switch]$KeepInstance,
    [int]$DiskGb = 80,
    [switch]$No3090Fallback
)

$ErrorActionPreference = "Stop"

$CptRootLocal = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$env:VAST_SESSION_FILE = Join-Path $CptRootLocal "kaggle\runpod_cpt_v3\vast_cpt_s6\c_eval_session.json"
$env:VAST_LOCAL_RESULTS_DIR = Join-Path $CptRootLocal "kaggle\runpod_cpt_v3\vast_cpt_s6\c_eval"

. "$PSScriptRoot\vast_cpt_common.ps1"

$FtScripts = Join-Path $RepoRoot "fine_tuning\scripts"
$Script:DefaultLabel = "cpt-s6-c-eval"
$Script:DefaultDiskGb = $DiskGb
$Script:MaxWallHours = 4
$Script:SearchQuery = "num_gpus=1 gpu_name=RTX_4090 reliability>=0.90 disk_space>=60 gpu_frac>=1 cuda_max_good>=12.6"
$Script:SearchQuery3090 = "num_gpus=1 gpu_name=RTX_3090 reliability>=0.90 disk_space>=60 gpu_frac>=1 cuda_max_good>=12.6"

$ExpectedSha = "6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c"
$AdapterDir = Join-Path $CptRoot "kaggle\runpod_cpt_v3\vast_cpt_s6\fetch\theology_cpt_lora\theology_cpt_lora"
$Holdouts = Join-Path $CptRoot "kaggle\a_output_v3\theology_holdouts"
$Mcq = Join-Path $CptRoot "data\catechism_mcq.json"
$EvalPy = Join-Path $CptRoot "scripts\eval_cpt_sota.py"
$RemoteSh = Join-Path $CptRoot "scripts\vast_remote_c_eval.sh"
$ResultsDir = $env:VAST_LOCAL_RESULTS_DIR

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null

function Invoke-CEvalSsh([string]$Remote) {
    $session = Get-VastSession
    if (-not $session -or -not $session.ssh_host) { throw "No SSH session for C-eval" }
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

Write-Host "=== Vast S6 C-eval (ckpt-2050 LoRA) ==="
Write-Host "disk=${DiskGb}GB label=$DefaultLabel expected_sha=$ExpectedSha"

# --- Local preflight ---
foreach ($p in @($AdapterDir, $Holdouts, $Mcq, $EvalPy, $RemoteSh)) {
    if (-not (Test-Path $p)) { throw "Missing artifact: $p" }
}
$weights = Join-Path $AdapterDir "adapter_model.safetensors"
$gotSha = (Get-FileHash -Algorithm SHA256 -Path $weights).Hash.ToLower()
if ($gotSha -ne $ExpectedSha) {
    throw "Local adapter SHA mismatch want=$ExpectedSha got=$gotSha"
}
Write-Host "Local adapter SHA OK"

Show-VastAccountSummary
$user = Invoke-VastaiJson -CliArgs @("show", "user")
$credit = [double]$user.credit
if ($credit -lt 3.0) {
    throw "Vast credit=$credit too low for C-eval (need ~`$3+)"
}

$instText = Invoke-Vastai -CliArgs @("show", "instances") -RawJson
if ($instText -notmatch '^\s*\[\s*\]\s*$') {
    throw "Leftover Vast instances present - destroy before C-eval rent"
}

# --- Pick offer (prefer EU/US/CA; skip slow Asia hosts that flake on long SSH) ---
function Test-VastCEvalGeoOk([string]$Geo) {
    if (-not $Geo) { return $false }
    $g = $Geo.ToLowerInvariant()
    foreach ($bad in @("thailand", "taiwan", "india", "vietnam", "indonesia", "china", "tw,", " th", ", th", " in,", ", in")) {
        if ($g.Contains($bad.Trim())) { return $false }
    }
    foreach ($good in @("hungary", "netherlands", "germany", "france", "poland", "czech", "romania", "sweden", "finland", "united states", "usa", "canada", "uk,", "united kingdom", "portugal", "spain", "italy", "belgium", "austria", "norway", "ireland", "iceland", "bulgaria", "slovakia", "slovenia", "estonia", "latvia", "lithuania")) {
        if ($g.Contains($good)) { return $true }
    }
    # Unknown geo: allow if not clearly Asia
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
        if (Test-VastCEvalGeoOk $geo) { $pick = $o; break }
        Write-Host "Skip slow/risky geo=$geo offer=$($o.id)"
    }
    if (-not $pick) { $pick = $fallback }

    if (-not $pick -and -not $No3090Fallback) {
        Write-Host "Falling back to RTX 3090 search ..."
        $offers = @(Find-VastCheapestOffer -Query $SearchQuery3090 -Limit 15)
        foreach ($o in $offers) {
            $dphCand = if ($o.dph_total) { [double]$o.dph_total } else { [double]$o.dph }
            if ($dphCand -le 0 -or $dphCand -ge 0.8) { continue }
            if (Test-VastCEvalGeoOk ([string]$o.geolocation)) { $pick = $o; break }
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

# --- Provision ---
Write-Host "Renting offer=$OfferId ..."
& (Join-Path $FtScripts "vast_provision.ps1") -OfferId $OfferId -DiskGb $DiskGb -Label $DefaultLabel -Force
if ($LASTEXITCODE -ne 0) { throw "provision failed" }

$session = Get-VastSession
$ht = Convert-SessionToHashtable $session
$ht.name = $DefaultLabel
$ht.max_wall_hours = $MaxWallHours
$ht.c_eval_adapter_sha = $ExpectedSha
$ht.c_eval_status = "provisioned"
Save-VastSession $ht

& (Join-Path $FtScripts "vast_wait_ssh.ps1")
if ($LASTEXITCODE -ne 0) { throw "wait_ssh failed" }
& (Join-Path $FtScripts "vast_verify_gpu.ps1")
if ($LASTEXITCODE -ne 0) { throw "verify_gpu failed" }

$session = Get-VastSession
& (Join-Path $FtScripts "vast_inject_hf_token.ps1")
if ($LASTEXITCODE -ne 0) { Write-Host "WARN: HF inject failed - continuing" }

# --- Sync assets ---
Write-Host "Syncing C-eval assets ..."
Invoke-CEvalSsh "mkdir -p /workspace/hf_home && rm -rf /workspace/theology_cpt_lora /workspace/theology_holdouts"
# Inner nested LoRA dir is already named theology_cpt_lora - land under /workspace/
Send-ToWorkspace $AdapterDir "/workspace/"
Invoke-CEvalSsh 'if [[ -f /workspace/theology_cpt_lora/adapter_model.safetensors ]]; then echo LORA_LAYOUT_OK; elif [[ -f /workspace/theology_cpt_lora/theology_cpt_lora/adapter_model.safetensors ]]; then mv /workspace/theology_cpt_lora/theology_cpt_lora/* /workspace/theology_cpt_lora/ && rmdir /workspace/theology_cpt_lora/theology_cpt_lora 2>/dev/null; echo LORA_LAYOUT_FLATTENED; else echo LORA_LAYOUT_FAIL; ls -laR /workspace/theology_cpt_lora || true; exit 2; fi'
Send-ToWorkspace $Holdouts "/workspace/"
Send-ToWorkspace $Mcq "/workspace/catechism_mcq.json"
Send-ToWorkspace $EvalPy "/workspace/eval_cpt_sota.py"
Send-ToWorkspace $RemoteSh "/workspace/vast_remote_c_eval.sh"
Invoke-CEvalSsh "chmod +x /workspace/vast_remote_c_eval.sh && test -f /workspace/theology_cpt_lora/adapter_model.safetensors && test -d /workspace/theology_holdouts/spurgeon && echo REMOTE_LAYOUT_OK"
if ($Script:LastRemoteExit -ne 0) { throw "remote layout check failed" }

$ht = Convert-SessionToHashtable (Get-VastSession)
$ht.c_eval_status = "running"
Save-VastSession $ht

# --- Run C-eval via nohup + poll (SSH drops must not kill install/eval) ---
Write-Host "Launching C-eval nohup on remote (Miniforge + eval; poll up to 3h) ..."
# Fresh local metrics so a prior fail cannot look like success
Remove-Item (Join-Path $ResultsDir "theology_cpt_eval_metrics.json") -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $ResultsDir "cpt_eval.log") -Force -ErrorAction SilentlyContinue
Invoke-CEvalSsh "rm -f /workspace/cpt_eval.log /workspace/theology_cpt_eval_metrics.json /workspace/c_eval_done.txt /workspace/c_eval_rc.txt /workspace/c_eval_launcher.log; export EXPECTED_ADAPTER_SHA256=$ExpectedSha; nohup bash -lc 'bash /workspace/vast_remote_c_eval.sh; echo `$? > /workspace/c_eval_rc.txt; date -u > /workspace/c_eval_done.txt' > /workspace/c_eval_launcher.log 2>&1 & echo LAUNCHED"
$deadline = (Get-Date).AddHours(3)
$rc = -1
$done = $false
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 60
    $session = Get-VastSession
    if (-not $session.ssh_host) { Write-Host "poll: SSH lost"; break }
    $sshArgs = (Get-VastSshArgs $session) + @(
        (Get-VastSshRemote $session),
        "if [[ -f /workspace/c_eval_done.txt ]]; then echo C_EVAL_DONE; cat /workspace/c_eval_rc.txt; elif pgrep -f vast_remote_c_eval.sh >/dev/null || pgrep -f eval_cpt_sota.py >/dev/null; then echo C_EVAL_RUNNING; tail -n 2 /workspace/cpt_eval.log 2>/dev/null || tail -n 2 /workspace/c_eval_launcher.log 2>/dev/null || true; else echo C_EVAL_IDLE; tail -n 5 /workspace/c_eval_launcher.log 2>/dev/null || true; fi"
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
    if ($flat.Length -gt 200) { $flat = $flat.Substring(0, 200) }
    Write-Host ("poll: " + $flat)
    if ($pollOut -match "C_EVAL_DONE") {
        $done = $true
        foreach ($ln in ($pollOut -split "`n")) {
            $t = $ln.Trim()
            if ($t -match '^\d+$') { $rc = [int]$t; break }
        }
        break
    }
}
if (-not $done) {
    Write-Host "WARN: poll deadline reached or SSH lost without c_eval_done.txt"
    if ($rc -lt 0) { $rc = 124 }
}
Write-Host "remote exit=$rc"

# --- Fetch ---
$session = Get-VastSession
$port = Get-VastSshPort $session
$target = Get-VastSshRemote $session
$scpBase = @("-i", $SshKey, "-P", "$port", "-o", "StrictHostKeyChecking=accept-new")
$prevErr = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& scp @($scpBase + @("${target}:/workspace/cpt_eval.log", (Join-Path $ResultsDir "cpt_eval.log"))) 2>$null
& scp @($scpBase + @("${target}:/workspace/theology_cpt_eval_metrics.json", (Join-Path $ResultsDir "theology_cpt_eval_metrics.json"))) 2>$null
$ErrorActionPreference = $prevErr
$stamp = Get-Date -Format o
@"
remote_exit=$rc
adapter_sha=$ExpectedSha
fetched=$stamp
"@ | Set-Content (Join-Path $ResultsDir "result.txt")
Write-Host "Eval artifacts -> $ResultsDir"

$metricsPath = Join-Path $ResultsDir "theology_cpt_eval_metrics.json"
$ok = (Test-Path $metricsPath) -and ($rc -eq 0)

$ht = Convert-SessionToHashtable (Get-VastSession)
$ht.c_eval_status = if ($ok) { "complete" } else { "failed" }
$ht.c_eval_remote_exit = $rc
$ht.c_eval_fetched_at = $stamp
Save-VastSession $ht

if (-not $KeepInstance) {
    Write-Host "Destroying Vast instance ..."
    & (Join-Path $FtScripts "vast_destroy.ps1")
}

if ($ok) {
    Write-Host "RESULT: C-EVAL COMPLETE - metrics at $metricsPath"
    exit 0
}
Write-Host "RESULT: C-EVAL FAIL rc=$rc metrics_present=$(Test-Path $metricsPath)"
exit 1
