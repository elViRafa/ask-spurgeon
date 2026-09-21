# Runpod stack-isolation C: score nested S6 SHA 6aab on S5/Hub-v2 stack (torch 2.8 + Unsloth 2026.8.22).
# Does NOT use s6_run_c_eval.ps1 (that scores live checkpoints_sota). No training. No Hub overwrite.
param(
    [string]$PodId = "",
    [string]$SshHost = "",
    [int]$SshPort = 22,
    [switch]$SkipSync,
    [switch]$SkipFetch,
    [switch]$KeepPod
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot\s6_runpod_common.ps1"

$ExpectedSha = "6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c"
$UnslothPin = "unsloth[colab-new]==2026.8.22"
$AdapterDir = Join-Path $CptRoot "kaggle\runpod_cpt_v3\vast_cpt_s6\fetch\theology_cpt_lora\theology_cpt_lora"
$Holdouts = Join-Path $CptRoot "kaggle\a_output_v3\theology_holdouts"
$Mcq = Join-Path $CptRoot "data\catechism_mcq.json"
$EvalPy = Join-Path $CptRoot "scripts\eval_cpt_sota.py"
$RemoteSh = Join-Path $CptRoot "scripts\runpod_remote_stack_isolation_c.sh"
$ResultsDir = Join-Path $CptRoot "kaggle\runpod_cpt_v3\stack_isolation_c"
$SessionFile = Join-Path $CptRoot "kaggle\runpod_cpt_v3\stack_isolation_c_session.json"

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null

function Save-StackSession([hashtable]$Data) {
    ($Data | ConvertTo-Json -Depth 6) | Set-Content -Path $SessionFile -Encoding UTF8
}

function Get-StackSession {
    if (-not (Test-Path $SessionFile)) { return $null }
    return Get-Content $SessionFile -Raw | ConvertFrom-Json
}

# --- Local preflight ---
foreach ($p in @($AdapterDir, $Holdouts, $Mcq, $EvalPy, $RemoteSh)) {
    if (-not (Test-Path $p)) { throw "Missing artifact: $p" }
}
$weights = Join-Path $AdapterDir "adapter_model.safetensors"
$gotSha = (Get-FileHash -Algorithm SHA256 -Path $weights).Hash.ToLower()
if ($gotSha -ne $ExpectedSha) {
    throw "Local adapter SHA mismatch want=$ExpectedSha got=$gotSha"
}
Write-Host "Local nested adapter SHA OK ($ExpectedSha)"
Write-Host "Stack pin: torch image 2.8 + $UnslothPin (from S5 cpt_eval.log Unsloth 2026.8.22)"

if (-not $PodId -or -not $SshHost) {
    $sess = Get-StackSession
    if ($sess) {
        if (-not $PodId) { $PodId = [string]$sess.pod_id }
        if (-not $SshHost) { $SshHost = [string]$sess.ssh_host }
        if ($SshPort -eq 22 -and $sess.ssh_port) { $SshPort = [int]$sess.ssh_port }
    }
}
if (-not $PodId -or -not $SshHost) {
    throw "Provide -PodId and -SshHost (or populate $SessionFile after MCP create)."
}

$sshTarget = "root@$SshHost"
$sshArgs = @("-i", $SshKey, "-p", "$SshPort", "-o", "StrictHostKeyChecking=accept-new")
$scpArgsBase = @("-i", $SshKey, "-P", "$SshPort", "-o", "StrictHostKeyChecking=accept-new")

Save-StackSession @{
    pod_id = $PodId
    ssh_host = $SshHost
    ssh_port = $SshPort
    expected_sha = $ExpectedSha
    unsloth_pip_spec = $UnslothPin
    train_probe_docs = 16
    started_at = (Get-Date).ToString("o")
}

Write-Host "=== Stack-isolation C on $sshTarget port=$SshPort pod=$PodId ==="

if (-not $SkipSync) {
    Write-Host "Syncing nested LoRA + v3 holdouts + eval..."
    & ssh @($sshArgs + @($sshTarget, "mkdir -p /workspace/theology_cpt_lora /workspace/hf_home"))
    if ($LASTEXITCODE -ne 0) { throw "ssh mkdir failed" }

    # Nested adapter files into /workspace/theology_cpt_lora/ (not outer stale S5).
    & scp @($scpArgsBase + @("-r", "$AdapterDir\*", "${sshTarget}:/workspace/theology_cpt_lora/"))
    if ($LASTEXITCODE -ne 0) { throw "scp adapter failed" }
    # Creates /workspace/theology_holdouts/{spurgeon,...}
    & scp @($scpArgsBase + @("-r", $Holdouts, "${sshTarget}:/workspace/"))
    if ($LASTEXITCODE -ne 0) { throw "scp holdouts failed" }
    & scp @($scpArgsBase + @($Mcq, "${sshTarget}:/workspace/catechism_mcq.json"))
    if ($LASTEXITCODE -ne 0) { throw "scp mcq failed" }
    & scp @($scpArgsBase + @($EvalPy, "${sshTarget}:/workspace/eval_cpt_sota.py"))
    if ($LASTEXITCODE -ne 0) { throw "scp eval failed" }
    & scp @($scpArgsBase + @($RemoteSh, "${sshTarget}:/workspace/runpod_remote_stack_isolation_c.sh"))
    if ($LASTEXITCODE -ne 0) { throw "scp remote sh failed" }
    & ssh @($sshArgs + @($sshTarget, "chmod +x /workspace/runpod_remote_stack_isolation_c.sh"))
    Write-Host "Sync OK"
}

Write-Host "Launching remote C (pinned Unsloth + 16-doc train probe)..."
$remoteCmd = @"
export EXPECTED_ADAPTER_SHA256=$ExpectedSha
export UNSLOTH_PIP_SPEC='$UnslothPin'
export CPT_EVAL_TRAIN_PROBE_DOCS=16
bash /workspace/runpod_remote_stack_isolation_c.sh
"@
& ssh @($sshArgs + @($sshTarget, $remoteCmd))
$evalRc = $LASTEXITCODE
Write-Host "Remote C exit=$evalRc"

if (-not $SkipFetch) {
    Write-Host "Fetching metrics + log -> $ResultsDir"
    & scp @($scpArgsBase + @("${sshTarget}:/workspace/cpt_eval.log", $ResultsDir))
    & scp @($scpArgsBase + @("${sshTarget}:/workspace/theology_cpt_eval_metrics.json", $ResultsDir))
    # Pin note
    @"
# Stack isolation C pin note
expected_sha=$ExpectedSha
unsloth=$UnslothPin
torch_image=runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404
train_probe_docs=16
holdouts=a_output_v3
adapter=vast_cpt_s6/fetch/theology_cpt_lora/theology_cpt_lora
pod_id=$PodId
remote_exit=$evalRc
fetched_at=$((Get-Date).ToString('o'))
"@ | Set-Content -Path (Join-Path $ResultsDir "STACK_PIN.txt") -Encoding UTF8
}

if (-not $KeepPod) {
    Write-Host "Terminate pod $PodId via REST (or MCP pod-action terminate) when fetch OK."
    Write-Host "HINT: use Runpod MCP pod-action action=terminate on this pod id."
}

if ($evalRc -ne 0) { throw "Stack-isolation C failed rc=$evalRc" }
Write-Host "DONE. Inspect $ResultsDir\theology_cpt_eval_metrics.json"
