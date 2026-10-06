# Vast S8 m_hi resume isolation C.
# Flat theology_cpt_lora SHA 2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207
# (same bytes as checkpoint-2250). AdapterDir is the flat leaf, not the checkpoint dir.
# Stack: Unsloth 2026.8.22 + torch 2.8 via vast_remote_stack_isolation_c.sh.
# Do NOT use vast_remote_c_eval.sh (S6 torch 2.11).
# Do NOT score Phase A 06354dfc, S6 6aab, S7 replay/Phase B, or merge-parent a70fded8 as the C candidate.
# Holdouts: a_output_v6_p0. No training. No Hub overwrite.
# C rebuilds /workspace/theology_cpt_merged_a70 on the pod from a70 + merge_cpt_lora.py
# (adapter_config names that path). Do NOT remap adapter onto stock Qwen.
# Older "No merge" notes meant no Hub merge promote — not "skip pod-local merge parent".
# Default: readiness only (no vastai, no rent). -Go rents one GPU.
# Success destroys the instance unless -KeepInstance. Failure keeps it for inspection.
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

# Resume best checkpoint-2250 / 22698039. Not Phase A 06354dfc.
$ExpectedSha = "2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207"
$PhaseASha = "06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432"
$ForbiddenSha = @(
    $PhaseASha,
    "6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c",
    "ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303",
    "ddbbee3ac9ef7baf6cca21dcdb844d027d39f5f6a4b88ba10fcf8a43fa7c8214",
    "0289f1c9af70615ef4dca58b3e2d7dabc3eefef96c8bdf92bff0933689adeb55",
    "a70fded8aea1c9cb1a484e640e89137412519c28d95bdbfbf8d73ca2d2e42eac"
)
$AdapterDir = Join-Path $CptRootLocal "kaggle\runpod_cpt_v3\vast_cpt_s8_mhi_resume\fetch\mhi_resume\theology_cpt_lora"
$Holdouts = Join-Path $CptRootLocal "kaggle\a_output_v6_p0\theology_holdouts"
$Mcq = Join-Path $CptRootLocal "data\catechism_mcq.json"
$EvalPy = Join-Path $CptRootLocal "scripts\eval_cpt_sota.py"
$RemoteSh = Join-Path $CptRootLocal "scripts\vast_remote_stack_isolation_c.sh"
$ResultsDir = Join-Path $CptRootLocal "kaggle\runpod_cpt_v3\vast_cpt_s8_mhi_resume_c"
# Merge parent a70 (S7 P0 s5best). Not the C candidate — used only to rebuild theology_cpt_merged_a70 on the pod.
$MergeParentDir = Join-Path $CptRootLocal "kaggle\runpod_cpt_v3\vast_cpt_s7_p0\fetch\theology_cpt_lora_s5best"
$MergePy = Join-Path $RepoRootLocal "fine_tuning\scripts\merge_cpt_lora.py"
$MergeParentSha = "a70fded8aea1c9cb1a484e640e89137412519c28d95bdbfbf8d73ca2d2e42eac"

Write-Host "=== Vast S8 m_hi resume isolation C (flat ckpt-2250 22698039) ==="
Write-Host "go=$Go disk=${DiskGb}GB expected_sha=$ExpectedSha"
Write-Host "stack=Unsloth 2026.8.22 + torch 2.8.0+cu126 (NOT torch 2.11)"
Write-Host "adapter=$AdapterDir"
Write-Host "holdouts=$Holdouts"
Write-Host "merge_parent=$MergeParentDir"
Write-Host "merge_py=$MergePy"
Write-Host "results=$ResultsDir"

$py = Join-Path $RepoRootLocal ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
& $py (Join-Path $PSScriptRoot "vast_cpt_s8_mhi_resume_c_eval_readiness.py")
if ($LASTEXITCODE -ne 0) { throw "C-eval readiness FAIL" }

if (-not $Go) {
    Write-Host ""
    Write-Host "DRY COMPLETE -- readiness only. No GPU rent."
    Write-Host "Forge runs this only after Rafael says go:"
    Write-Host "  cd continued_pretrain\scripts"
    Write-Host "  .\vast_cpt_s8_mhi_resume_c_eval.ps1 -Go"
    exit 0
}

# --- -Go only: one GPU, then fetch, then destroy on success ---
$env:VAST_SESSION_FILE = Join-Path $CptRootLocal "kaggle\runpod_cpt_v3\vast_cpt_s8_mhi_resume_c_session.json"
$env:VAST_LOCAL_RESULTS_DIR = $ResultsDir

. "$PSScriptRoot\vast_cpt_common.ps1"

$FtScripts = Join-Path $RepoRoot "fine_tuning\scripts"
$Script:DefaultLabel = "cpt-s8-mhi-resume-c"
$Script:DefaultDiskGb = $DiskGb
$Script:MaxWallHours = 4
$Script:SearchQuery = "num_gpus=1 gpu_name=RTX_4090 reliability>=0.90 disk_space>=60 gpu_frac>=1 cuda_max_good>=12.6"
$Script:SearchQuery3090 = "num_gpus=1 gpu_name=RTX_3090 reliability>=0.90 disk_space>=60 gpu_frac>=1 cuda_max_good>=12.6"

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

foreach ($p in @($AdapterDir, $Holdouts, $Mcq, $EvalPy, $RemoteSh, $MergeParentDir, $MergePy)) {
    if (-not (Test-Path $p)) { throw "Missing artifact: $p" }
}
$weights = Join-Path $AdapterDir "adapter_model.safetensors"
$gotSha = (Get-FileHash -Algorithm SHA256 -Path $weights).Hash.ToLower()
if ($gotSha -eq $PhaseASha) {
    throw "Refusing Phase A 06354dfc for isolation C"
}
foreach ($bad in $ForbiddenSha) {
    if ($gotSha -eq $bad) {
        throw "Refusing non-resume adapter SHA $bad"
    }
}
if ($gotSha -ne $ExpectedSha) {
    throw "Local adapter SHA mismatch want=$ExpectedSha got=$gotSha"
}
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
    throw "Vast credit=$credit too low for C-eval (need ~`$2+)"
}

$instText = Invoke-Vastai -CliArgs @("show", "instances") -RawJson
if ($instText -notmatch '^\s*\[\s*\]\s*$') {
    throw "Leftover Vast instances present - destroy before C-eval rent"
}

function Test-VastCEvalGeoOk([string]$Geo) {
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

Write-Host "Syncing C-eval assets (m_hi resume flat 22698039 + merge parent a70) ..."
Invoke-CEvalSsh "mkdir -p /workspace/hf_home && rm -rf /workspace/theology_cpt_lora /workspace/theology_holdouts /workspace/merge_parent_a70 /workspace/theology_cpt_merged_a70"
Send-ToWorkspace $AdapterDir "/workspace/"
Invoke-CEvalSsh 'if [[ -f /workspace/theology_cpt_lora/adapter_model.safetensors ]]; then echo LORA_LAYOUT_OK; elif [[ -f /workspace/theology_cpt_lora/theology_cpt_lora/adapter_model.safetensors ]]; then mv /workspace/theology_cpt_lora/theology_cpt_lora/* /workspace/theology_cpt_lora/ && rmdir /workspace/theology_cpt_lora/theology_cpt_lora 2>/dev/null; echo LORA_LAYOUT_FLATTENED; else echo LORA_LAYOUT_FAIL; ls -laR /workspace/theology_cpt_lora 2>/dev/null || true; exit 2; fi'
Send-ToWorkspace $Holdouts "/workspace/"
Send-ToWorkspace $Mcq "/workspace/catechism_mcq.json"
Send-ToWorkspace $EvalPy "/workspace/eval_cpt_sota.py"
Send-ToWorkspace $RemoteSh "/workspace/vast_remote_stack_isolation_c.sh"
Invoke-CEvalSsh "rm -rf /workspace/merge_parent_a70 && mkdir -p /workspace/merge_parent_a70"
Send-ToWorkspace $MergeParentDir "/workspace/merge_parent_a70"
Invoke-CEvalSsh 'if [[ -f /workspace/merge_parent_a70/adapter_model.safetensors ]]; then echo MERGE_PARENT_LAYOUT_OK; elif [[ -f /workspace/merge_parent_a70/theology_cpt_lora_s5best/adapter_model.safetensors ]]; then mv /workspace/merge_parent_a70/theology_cpt_lora_s5best/* /workspace/merge_parent_a70/ && rmdir /workspace/merge_parent_a70/theology_cpt_lora_s5best 2>/dev/null; echo MERGE_PARENT_LAYOUT_FLATTENED; else echo MERGE_PARENT_LAYOUT_FAIL; ls -laR /workspace/merge_parent_a70 2>/dev/null || true; exit 2; fi'
Send-ToWorkspace $MergePy "/workspace/merge_cpt_lora.py"
Invoke-CEvalSsh "chmod +x /workspace/vast_remote_stack_isolation_c.sh && test -f /workspace/theology_cpt_lora/adapter_model.safetensors && test -d /workspace/theology_holdouts/spurgeon && test -f /workspace/merge_parent_a70/adapter_model.safetensors && test -f /workspace/merge_cpt_lora.py && echo REMOTE_LAYOUT_OK"
if ($Script:LastRemoteExit -ne 0) { throw "remote layout check failed" }

$ht = Convert-SessionToHashtable (Get-VastSession)
$ht.c_eval_status = "running"
Save-VastSession $ht

Write-Host "Launching C-eval nohup on remote (Miniforge + eval; poll up to 3h) ..."
Remove-Item (Join-Path $ResultsDir "theology_cpt_eval_metrics.json") -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $ResultsDir "cpt_eval.log") -Force -ErrorAction SilentlyContinue
Invoke-CEvalSsh "rm -f /workspace/cpt_eval.log /workspace/theology_cpt_eval_metrics.json /workspace/c_eval_done.txt /workspace/c_eval_rc.txt /workspace/c_eval_launcher.log; export EXPECTED_ADAPTER_SHA256=$ExpectedSha; export MERGE_PARENT_DIR=/workspace/merge_parent_a70; export MERGE_PARENT_SHA=$MergeParentSha; export CPT_MERGED_BASE=/workspace/theology_cpt_merged_a70; export UNSLOTH_PIP_SPEC='unsloth[colab-new]==2026.8.22'; export CPT_EVAL_TRAIN_PROBE_DOCS=16; nohup bash -lc 'bash /workspace/vast_remote_stack_isolation_c.sh; echo `$? > /workspace/c_eval_rc.txt; date -u > /workspace/c_eval_done.txt' > /workspace/c_eval_launcher.log 2>&1 & echo LAUNCHED"
$deadline = (Get-Date).AddHours(3)
$rc = -1
$done = $false
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 60
    $session = Get-VastSession
    if (-not $session.ssh_host) { Write-Host "poll: SSH lost"; break }
    $sshArgs = (Get-VastSshArgs $session) + @(
        (Get-VastSshRemote $session),
        "if [[ -f /workspace/c_eval_done.txt ]]; then echo C_EVAL_DONE; cat /workspace/c_eval_rc.txt; elif pgrep -f vast_remote_stack_isolation_c.sh >/dev/null || pgrep -f eval_cpt_sota.py >/dev/null; then echo C_EVAL_RUNNING; tail -n 2 /workspace/cpt_eval.log 2>/dev/null || tail -n 2 /workspace/c_eval_launcher.log 2>/dev/null || true; else echo C_EVAL_IDLE; tail -n 5 /workspace/c_eval_launcher.log 2>/dev/null || true; fi"
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

$session = Get-VastSession
$port = Get-VastSshPort $session
$target = Get-VastSshRemote $session
$scpBase = @("-i", $SshKey, "-P", "$port", "-o", "StrictHostKeyChecking=accept-new")
$prevErr = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& scp @($scpBase + @("${target}:/workspace/cpt_eval.log", (Join-Path $ResultsDir "cpt_eval.log"))) 2>$null
& scp @($scpBase + @("${target}:/workspace/theology_cpt_eval_metrics.json", (Join-Path $ResultsDir "theology_cpt_eval_metrics.json"))) 2>$null
& scp @($scpBase + @("${target}:/workspace/c_eval_launcher.log", (Join-Path $ResultsDir "c_eval_launcher.log"))) 2>$null
& scp @($scpBase + @("${target}:/workspace/c_eval_rc.txt", (Join-Path $ResultsDir "c_eval_rc.txt"))) 2>$null
$ErrorActionPreference = $prevErr
$stamp = Get-Date -Format o
@"
remote_exit=$rc
adapter_sha=$ExpectedSha
adapter=vast_cpt_s8_mhi_resume/fetch/mhi_resume/theology_cpt_lora
step=2250
fetched=$stamp
unsloth=unsloth[colab-new]==2026.8.22
torch=2.8.0+cu126
train_probe_docs=16
holdouts=a_output_v6_p0
merge_parent=a70fded8
eval_base=unsloth/Qwen3.5-4B-Base
note=S8 m_hi resume isolation C on flat theology_cpt_lora checkpoint-2250 22698039; pod rebuilds theology_cpt_merged_a70 from a70 before from_pretrained
section5_puritan_loss_max=1.6349
hub_until_win=06354dfc
"@ | Set-Content (Join-Path $ResultsDir "result.txt")
@"
# Stack isolation pin (torch 2.8, not S6 torch 2.11)
unsloth=2026.8.22
torch=2.8.0+cu126
expected_sha=$ExpectedSha
train_probe_docs=16
run=s8-mhi-resume-isolation-c
"@ | Set-Content (Join-Path $ResultsDir "STACK_PIN.txt")
Write-Host "Eval artifacts -> $ResultsDir"

$metricsPath = Join-Path $ResultsDir "theology_cpt_eval_metrics.json"
$ok = (Test-Path $metricsPath) -and ($rc -eq 0)

$ht = Convert-SessionToHashtable (Get-VastSession)
$ht.c_eval_status = if ($ok) { "complete" } else { "failed" }
$ht.c_eval_remote_exit = $rc
$ht.c_eval_fetched_at = $stamp
Save-VastSession $ht

if (-not $KeepInstance) {
    if (-not $ok) {
        Write-Host "KEEPING instance after FAIL so launcher log can be inspected (pass without fail to auto-destroy, or run vast_destroy.ps1)."
        Write-Host "HINT: scp c_eval_launcher.log then .\fine_tuning\scripts\vast_destroy.ps1"
    }
    else {
        Write-Host "Destroying Vast instance ..."
        & (Join-Path $FtScripts "vast_destroy.ps1")
    }
}

if ($ok) {
    Write-Host "RESULT: C-EVAL COMPLETE - metrics at $metricsPath"
    Write-Host "Section 5 win only if puritan loss <= 1.6349 and Spurgeon is not worse than stock base. Else keep Hub 06354dfc."
    exit 0
}
Write-Host "RESULT: C-EVAL FAIL rc=$rc metrics_present=$(Test-Path $metricsPath)"
exit 1
