# SSH to pod and start SFT GATE-0 training.
. "$PSScriptRoot\sft_runpod_common.ps1"

$session = Get-SftSession
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready - run sft_wait_ssh.ps1 first"
}

$port = Get-SftSshPort $session
$sshTarget = Get-SftSshRemote $session
$sshArgs = @("-i", $SshKey, "-p", "$port", "-o", "StrictHostKeyChecking=accept-new", $sshTarget, "bash -lc 'source /workspace/.sft_env 2>/dev/null || true; bash /workspace/sft_remote_train.sh'")

& ssh @sshArgs
if ($LASTEXITCODE -ne 0) { throw "Remote launch failed" }
Write-Host "Verify log gates in sft_train.log before walk-away."
