# Confirm nvidia-smi on the Vultr GPU VM. Exit 2 if missing (caller should destroy).
. "$PSScriptRoot\vultr_common.ps1"

$session = Get-VultrSession
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready"
}

$sshArgs = (Get-VultrSshArgs $session) + @((Get-VultrSshRemote $session), "nvidia-smi")
& ssh @sshArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "nvidia-smi failed - GPU drivers missing. Destroy this instance (do not idle-bill)."
    exit 2
}
Write-Host "nvidia-smi OK"
exit 0
