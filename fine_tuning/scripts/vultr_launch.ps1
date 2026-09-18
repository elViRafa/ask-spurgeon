# Detach GATE-0 setup -> merge -> train on the Vultr VM.
. "$PSScriptRoot\vultr_common.ps1"

$session = Get-VultrSession
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready - run vultr_wait_ssh.ps1 first"
}

$sshTarget = Get-VultrSshRemote $session
$sshArgs = Get-VultrSshArgs $session
$remote = @'
set -euo pipefail
source /workspace/.sft_env 2>/dev/null || true
chmod +x /workspace/sft_remote_setup.sh /workspace/sft_remote_train.sh /workspace/sft_remote_merge.sh
if pgrep -f "sft_remote_train.sh" >/dev/null 2>&1; then
  echo "sft_remote_train.sh already running"
  pgrep -af sft_remote_train.sh || true
  exit 0
fi
nohup bash /workspace/sft_remote_train.sh > /workspace/sft_launch.log 2>&1 &
echo "LAUNCH_PID $!"
sleep 3
tail -n 30 /workspace/sft_launch.log || true
'@

& ssh @($sshArgs + @($sshTarget, $remote))
if ($LASTEXITCODE -ne 0) { throw "Remote launch failed" }
Write-Host "Detached launch started. Tail /workspace/sft_launch.log and /workspace/sft_train.log"
