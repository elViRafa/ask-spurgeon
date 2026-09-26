# Copy S7 replay artifacts (a_output_v6 + Phase B C-winner ddbbee3a) to a Vast instance. Requires SSH. Does NOT start train.
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\vast_cpt_s7_common.ps1"

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

$mixDir = Get-VastCptS7MixDir
$dataset = Join-Path $mixDir "theology_dataset"
$holdouts = Join-Path $mixDir "theology_holdouts"
$manifest = Join-Path $CptRoot "data\mix_v6\theology_mix_manifest.json"
$lora = Get-VastCptS7LoraDir
$train = Join-Path $CptRoot "scripts\train_cpt_sota.py"
$runtime = Join-Path $CptRoot "scripts\cpt_runtime.py"
$remoteSh = Join-Path $CptRoot "scripts\vast_cpt_s7_remote_continue_b.sh"
$payload = Join-Path $env:VAST_LOCAL_RESULTS_DIR "payload.tar"

foreach ($p in @($dataset, $holdouts, $manifest, $lora, $train, $runtime, $remoteSh)) {
    if (-not (Test-Path $p)) { throw "Missing artifact: $p" }
}
if (-not (Test-Path (Join-Path $lora "adapter_model.safetensors"))) {
    throw "Missing adapter at $lora"
}

Invoke-CptSsh "mkdir -p /workspace/checkpoints_s7 /workspace/hf_home"

if (Test-Path $payload) {
    Write-Host "Uploading packed payload.tar ..."
    Send-ToWorkspace $payload "/workspace/payload.tar"
    Invoke-CptSsh "tar -xf /workspace/payload.tar -C /workspace && rm -f /workspace/payload.tar && chmod +x /workspace/vast_cpt_s7_remote_continue_b.sh && rm -rf /workspace/checkpoints_sota"
}
else {
    Send-ToWorkspace $dataset "/workspace/"
    Send-ToWorkspace $holdouts "/workspace/"
    Send-ToWorkspace $manifest "/workspace/theology_mix_manifest.json"
    # Inner dir leaf is theology_cpt_lora → /workspace/theology_cpt_lora/adapter_*.safetensors
    Invoke-CptSsh "rm -rf /workspace/theology_cpt_lora"
    Send-ToWorkspace $lora "/workspace/theology_cpt_lora"
    Send-ToWorkspace $train "/workspace/train_cpt_sota.py"
    Send-ToWorkspace $runtime "/workspace/cpt_runtime.py"
    Send-ToWorkspace $remoteSh "/workspace/vast_cpt_s7_remote_continue_b.sh"
    Invoke-CptSsh "chmod +x /workspace/vast_cpt_s7_remote_continue_b.sh && rm -rf /workspace/checkpoints_sota"
}

Write-Host "Verifying remote layout + adapter SHA ..."
$verify = @"
set -e
test -f /workspace/theology_dataset/dataset_dict.json
test -f /workspace/theology_cpt_lora/adapter_model.safetensors
test -f /workspace/train_cpt_sota.py
test -x /workspace/vast_cpt_s7_remote_continue_b.sh
test ! -d /workspace/checkpoints_sota
GOT=`$(sha256sum /workspace/theology_cpt_lora/adapter_model.safetensors | awk '{print `$1}')
WANT=$S7AdapterSha
echo GOT=`$GOT
test "`$GOT" = "`$WANT"
echo REMOTE_LAYOUT_OK
"@
Invoke-CptSsh $verify
Write-Host "Sync complete."
