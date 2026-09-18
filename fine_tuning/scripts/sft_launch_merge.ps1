# SSH to pod and run GATE-0 merge only.
. "$PSScriptRoot\sft_runpod_common.ps1"

$session = Get-SftSession
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready - run sft_wait_ssh.ps1 first"
}

$port = Get-SftSshPort $session
$sshTarget = Get-SftSshRemote $session
$sshArgs = @("-i", $SshKey, "-p", "$port", "-o", "StrictHostKeyChecking=accept-new", $sshTarget, "bash /workspace/sft_remote_merge.sh")

& ssh @sshArgs
if ($LASTEXITCODE -ne 0) { throw "Remote merge failed" }
