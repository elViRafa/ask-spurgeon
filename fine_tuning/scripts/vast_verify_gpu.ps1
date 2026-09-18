# Confirm nvidia-smi on the Vast GPU container. Exit 2 if missing.
. "$PSScriptRoot\vast_common.ps1"

$session = Get-VastSession
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready"
}

$sshArgs = (Get-VastSshArgs $session) + @((Get-VastSshRemote $session), "nvidia-smi")
& ssh @sshArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "nvidia-smi failed - GPU drivers missing. Destroy this instance (do not idle-bill)."
    exit 2
}
Write-Host "nvidia-smi OK"
exit 0
