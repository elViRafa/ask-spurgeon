# Copy full-corpus S6 artifacts to a Vast instance. Requires SSH session. Does NOT start train.
param(
    [switch]$SkipCheckpoint
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\vast_cpt_common.ps1"

$session = Get-VastSession
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready - run vast_wait_ssh.ps1 with VAST_SESSION_FILE set"
}

$port = Get-VastSshPort $session
$target = Get-VastSshRemote $session
$sshArgs = (Get-VastSshArgs $session)
$scpBase = @("-i", $SshKey, "-P", "$port", "-o", "StrictHostKeyChecking=accept-new")

function Invoke-CptSsh([string]$Remote) {
    & ssh @($sshArgs + @($target, $Remote))
    if ($LASTEXITCODE -ne 0) { throw "ssh failed: $Remote" }
}

function Send-ToWorkspace([string]$Local, [string]$Remote) {
    Write-Host "scp $Local -> ${target}:$Remote"
    & scp @($scpBase + @("-r", $Local, "${target}:$Remote"))
    if ($LASTEXITCODE -ne 0) { throw "scp failed: $Local" }
}

$dataset = Join-Path $CptRoot "kaggle\a_output_v3\theology_dataset"
$holdouts = Join-Path $CptRoot "kaggle\a_output_v3\theology_holdouts"
$manifest = Join-Path $CptRoot "data\theology_mix_manifest.json"
$lora = Join-Path $CptRoot "kaggle\runpod_cpt_v3\theology_cpt_lora"
$train = Join-Path $CptRoot "scripts\train_cpt_sota.py"
$runtime = Join-Path $CptRoot "scripts\cpt_runtime.py"
$remoteSh = Join-Path $CptRoot "scripts\vast_cpt_remote_continue_b.sh"
$ckpt = Get-VastCptResumeCkpt
$payload = Join-Path $env:VAST_LOCAL_RESULTS_DIR "payload.tar"

foreach ($p in @($dataset, $holdouts, $manifest, $lora, $train, $runtime, $remoteSh)) {
    if (-not (Test-Path $p)) { throw "Missing artifact: $p" }
}
if (-not $SkipCheckpoint -and -not (Test-Path $ckpt)) {
    throw "Missing resume checkpoint: $ckpt"
}

Invoke-CptSsh "mkdir -p /workspace/checkpoints_sota /workspace/hf_home"

if (Test-Path $payload) {
    Write-Host "Uploading packed payload.tar ..."
    Send-ToWorkspace $payload "/workspace/payload.tar"
    Invoke-CptSsh "tar -xf /workspace/payload.tar -C /workspace && rm -f /workspace/payload.tar && chmod +x /workspace/vast_cpt_remote_continue_b.sh"
}
else {
    Send-ToWorkspace $dataset "/workspace/"
    Send-ToWorkspace $holdouts "/workspace/"
    Send-ToWorkspace $manifest "/workspace/theology_mix_manifest.json"
    Send-ToWorkspace $lora "/workspace/"
    Send-ToWorkspace $train "/workspace/train_cpt_sota.py"
    Send-ToWorkspace $runtime "/workspace/cpt_runtime.py"
    Send-ToWorkspace $remoteSh "/workspace/vast_cpt_remote_continue_b.sh"
    if (-not $SkipCheckpoint) {
        Send-ToWorkspace $ckpt "/workspace/checkpoints_sota/"
    }
    Invoke-CptSsh "chmod +x /workspace/vast_cpt_remote_continue_b.sh"
}

Write-Host "Verifying remote layout ..."
Invoke-CptSsh "test -f /workspace/theology_dataset/dataset_dict.json && test -f /workspace/theology_cpt_lora/adapter_model.safetensors && test -f /workspace/train_cpt_sota.py && test -x /workspace/vast_cpt_remote_continue_b.sh && test -d /workspace/checkpoints_sota/checkpoint-2050 && echo REMOTE_LAYOUT_OK"
Write-Host "Sync complete."
