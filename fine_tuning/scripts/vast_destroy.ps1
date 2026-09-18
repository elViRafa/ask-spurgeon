# DESTROY the Vast GPU instance. Do not stop - stopped containers still cost storage.
param(
    [switch]$Force
)

. "$PSScriptRoot\vast_common.ps1"

$session = Get-VastSession
if (-not $session -or -not $session.instance_id) {
    Write-Host "No instance_id in session - nothing to destroy"
    exit 0
}

$id = [string]$session.instance_id
Write-Host "Destroying Vast instance $id ..."
try {
    Invoke-Vastai -CliArgs @("destroy", "instance", $id, "-y")
    Write-Host "Destroy requested"
}
catch {
    if (-not $Force) { throw }
    Write-Warning $_.Exception.Message
}

$ht = Convert-SessionToHashtable $session
$ht.instance_id = $null
$ht.ssh_host = $null
$ht.ssh_port = $null
$ht.ssh_url = $null
$ht.status = "destroyed"
$ht.destroyed_at = (Get-Date).ToUniversalTime().ToString("o")
Save-VastSession $ht
Write-Host "Session cleared"
