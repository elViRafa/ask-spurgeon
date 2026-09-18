# DELETE the Vultr GPU instance. Do not stop - stopped GPU VMs still cost.
param(
    [switch]$Force
)

. "$PSScriptRoot\vultr_common.ps1"

$session = Get-VultrSession
if (-not $session -or -not $session.instance_id) {
    if ($session -and $session.ssh_host -and -not $session.instance_id) {
        Write-Warning "Attach-only session (no instance_id). Destroy the VM in the Vultr console."
        exit 0
    }
    Write-Host "No instance_id in session - nothing to destroy"
    exit 0
}

$id = [string]$session.instance_id
Write-Host "Deleting Vultr instance $id ..."
try {
    Invoke-VultrApi -Method DELETE -Path "/instances/$id"
    Write-Host "Delete requested"
}
catch {
    if (-not $Force) { throw }
    Write-Warning $_.Exception.Message
}

$ht = @{}
$session.PSObject.Properties | ForEach-Object { $ht[$_.Name] = $_.Value }
$ht.instance_id = $null
$ht.ssh_host = $null
$ht.status = "deleted"
$ht.destroyed_at = (Get-Date).ToUniversalTime().ToString("o")
Save-VultrSession $ht
Write-Host "Session cleared"
