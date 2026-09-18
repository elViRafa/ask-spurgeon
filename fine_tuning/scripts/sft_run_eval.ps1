# SSH to pod and run F eval (EXPORT=False by default).
param(
    [switch]$Export
)

. "$PSScriptRoot\sft_runpod_common.ps1"

$session = Get-SftSession
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready - run sft_wait_ssh.ps1 first"
}

$exportVal = if ($Export) { "1" } else { "0" }
$port = Get-SftSshPort $session
$sshTarget = Get-SftSshRemote $session
$remote = @"
export SFT_WORK_ROOT=/workspace HF_HOME=/workspace/hf_home PYTHONUNBUFFERED=1
export USE_CPT_MERGE=1 SFT_GATE0_MERGED=/workspace/theology_cpt_v2_merged_hf
export SFT_EXPORT=$exportVal
python3 -u /workspace/eval_sft_sota.py
"@
$sshArgs = @("-i", $SshKey, "-p", "$port", "-o", "StrictHostKeyChecking=accept-new", $sshTarget, $remote)

& ssh @sshArgs
if ($LASTEXITCODE -ne 0) { throw "Remote eval failed" }
