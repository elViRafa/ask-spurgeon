# SSH to pod and start S6 continue-B training.
. "$PSScriptRoot\s6_runpod_common.ps1"

$session = Get-S6Session
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready - run s6_wait_ssh.ps1 first"
}

$port = Get-S6SshPort $session
$sshTarget = Get-S6SshRemote $session
$sshArgs = @("-i", $SshKey, "-p", "$port", "-o", "StrictHostKeyChecking=accept-new", $sshTarget, "bash /workspace/s6_remote_continue_b.sh")

& ssh @sshArgs
if ($LASTEXITCODE -ne 0) { throw "Remote launch failed" }
Write-Host "Verify log gates in cpt_train.log before walk-away."
