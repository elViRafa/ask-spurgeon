# Start S6 continue-B on a Vast instance that already has corpus + conda launcher synced.
# Does NOT provision. Next session only after operator -Go.
param(
    [switch]$Foreground
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\vast_cpt_common.ps1"

$session = Get-VastSession
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready"
}

$remote = Get-VastSshRemote $session
$sshArgs = (Get-VastSshArgs $session)
$cmd = "chmod +x /workspace/vast_cpt_remote_continue_b.sh; bash /workspace/vast_cpt_remote_continue_b.sh"
Write-Host "Launching continue-B on $remote ..."
if ($Foreground) {
    & ssh @($sshArgs + @($remote, $cmd))
    exit $LASTEXITCODE
}
& ssh @($sshArgs + @($remote, $cmd))
if ($LASTEXITCODE -ne 0) { throw "remote launch failed exit=$LASTEXITCODE" }
Write-Host "Launch command returned. Confirm walk-away gates in /workspace/cpt_train.log before leaving."
