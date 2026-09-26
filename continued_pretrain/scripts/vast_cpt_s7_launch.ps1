# Start S7 Phase A on a Vast instance that already has corpus + launcher synced.
param(
    [switch]$Foreground,
    [switch]$Resume
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\vast_cpt_s7_common.ps1"

$session = Get-VastSession
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready"
}

$remote = Get-VastSshRemote $session
$sshArgs = (Get-VastSshArgs $session)
$resumeEnv = if ($Resume) { "S7_RESUME=1 " } else { "" }
# Run the whole launcher under nohup so Miniforge/pip survives SSH disconnect.
# (Foreground install over SSH died mid-curl when the session dropped.)
$cmd = @"
chmod +x /workspace/vast_cpt_s7_remote_continue_b.sh
running_launcher() {
  pgrep -af 'vast_cpt_s7_remote_continue_b.sh' 2>/dev/null | grep -v 'pgrep\|bash -c\|nohup env' | grep -q .
}
running_train() {
  pgrep -af 'train_cpt_sota.py' 2>/dev/null | grep -v 'pgrep\|bash -c' | grep -q .
}
if running_launcher; then
  echo LAUNCHER_ALREADY_RUNNING
  tail -n 40 /workspace/s7_launcher.log 2>/dev/null || true
  exit 0
fi
if running_train; then
  echo TRAIN_ALREADY_RUNNING
  tail -n 40 /workspace/cpt_train.log 2>/dev/null || true
  exit 0
fi
nohup env ${resumeEnv}bash /workspace/vast_cpt_s7_remote_continue_b.sh > /workspace/s7_launcher.log 2>&1 &
echo LAUNCHER_PID=`$!
sleep 3
tail -n 40 /workspace/s7_launcher.log || true
"@
Write-Host "Launching S7 Phase A on $remote (nohup) ..."
if ($Foreground) {
    $fg = "chmod +x /workspace/vast_cpt_s7_remote_continue_b.sh; ${resumeEnv}bash /workspace/vast_cpt_s7_remote_continue_b.sh"
    & ssh @($sshArgs + @($remote, $fg))
    exit $LASTEXITCODE
}
& ssh @($sshArgs + @($remote, $cmd))
if ($LASTEXITCODE -ne 0) { throw "remote launch failed exit=$LASTEXITCODE" }
Write-Host "Launch command returned. Confirm walk-away gates in /workspace/s7_launcher.log and cpt_train.log."
