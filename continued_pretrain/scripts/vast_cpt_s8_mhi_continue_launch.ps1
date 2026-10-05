# Start the m_hi continue on a Vast instance that already has the payload synced.
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\vast_cpt_s8_mhi_continue_common.ps1"

$session = Get-VastSession
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready"
}

$remote = Get-VastSshRemote $session
$sshArgs = (Get-VastSshArgs $session)
$cmd = @"
chmod +x /workspace/vast_cpt_s8_mhi_continue_remote.sh
if pgrep -af 'vast_cpt_s8_mhi_continue_remote.sh' 2>/dev/null | grep -v 'pgrep\|bash -c\|nohup env' | grep -q .; then
  echo LAUNCHER_ALREADY_RUNNING
  tail -n 40 /workspace/mhi_continue_launcher.log 2>/dev/null || true
  exit 0
fi
if pgrep -af 'train_cpt_sota.py' 2>/dev/null | grep -v 'pgrep\|bash -c' | grep -q .; then
  echo TRAIN_ALREADY_RUNNING
  exit 0
fi
nohup env MERGE_ADAPTER_SHA256=$MergeAdapterSha INIT_ADAPTER_SHA256=$InitAdapterSha bash /workspace/vast_cpt_s8_mhi_continue_remote.sh > /workspace/mhi_continue_launcher.log 2>&1 &
echo LAUNCHER_PID=`$!
sleep 3
tail -n 40 /workspace/mhi_continue_launcher.log || true
"@
Write-Host "Launching m_hi continue on $remote (nohup) ..."
& ssh @($sshArgs + @($remote, $cmd))
if ($LASTEXITCODE -ne 0) { throw "remote launch failed exit=$LASTEXITCODE" }
Write-Host "Launch command returned. Confirm PIN_OK and ARM_START m_hi_continue in /workspace/mhi_continue_launcher.log."
