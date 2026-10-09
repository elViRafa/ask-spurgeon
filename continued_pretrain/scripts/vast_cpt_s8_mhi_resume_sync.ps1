# Copy the m_hi resume payload to a Vast instance. Requires SSH. Does not start training.
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\vast_cpt_s8_mhi_resume_common.ps1"

$session = Get-VastSession
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready - run vast_wait_ssh.ps1 with VAST_SESSION_FILE set"
}

$port = Get-VastSshPort $session
$target = Get-VastSshRemote $session
$sshArgs = (Get-VastSshArgs $session)
$scpBase = @("-i", $SshKey, "-P", "$port", "-o", "StrictHostKeyChecking=accept-new")
$payload = Join-Path $env:VAST_LOCAL_RESULTS_DIR "payload.tar"
if (-not (Test-Path $payload)) { throw "Missing payload.tar - run vast_cpt_s8_mhi_resume_pack.ps1 first" }

function Invoke-CptSsh([string]$Remote) {
    & ssh @($sshArgs + @($target, $Remote))
    if ($LASTEXITCODE -ne 0) { throw "ssh failed: $Remote" }
}

Write-Host "scp $payload -> ${target}:/workspace/payload.tar"
& scp @($scpBase + @($payload, "${target}:/workspace/payload.tar"))
if ($LASTEXITCODE -ne 0) { throw "scp failed" }

Invoke-CptSsh "mkdir -p /workspace/hf_home /workspace/mhi_resume && tar -xf /workspace/payload.tar -C /workspace && rm -f /workspace/payload.tar && chmod +x /workspace/vast_cpt_s8_mhi_resume_remote.sh && rm -rf /workspace/checkpoints_sota"

$verify = @"
set -e
test -f /workspace/theology_dataset/dataset_dict.json
test -f /workspace/theology_cpt_lora/adapter_model.safetensors
test -f /workspace/ckpt800/adapter_model.safetensors
test -f /workspace/ckpt800/optimizer.pt
test -f /workspace/ckpt800/rng_state.pth
test -f /workspace/train_cpt_sota.py
test -f /workspace/merge_cpt_lora.py
test -f /workspace/vast_cpt_s8_mhi_resume_plan.py
test -x /workspace/vast_cpt_s8_mhi_resume_remote.sh
test ! -d /workspace/checkpoints_sota
MERGE=`$(sha256sum /workspace/theology_cpt_lora/adapter_model.safetensors | awk '{print `$1}')
INIT=`$(sha256sum /workspace/ckpt800/adapter_model.safetensors | awk '{print `$1}')
echo MERGE=`$MERGE
echo INIT=`$INIT
test "`$MERGE" = "$MergeAdapterSha"
test "`$INIT" = "$InitAdapterSha"
echo REMOTE_LAYOUT_OK
"@
Invoke-CptSsh $verify
Write-Host "Sync complete."
