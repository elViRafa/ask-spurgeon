# Create Vultr Cloud GPU instance for GATE-0 merge + SFT. Destroys nothing.
param(
    [string]$Plan = "",
    [string]$Region = "",
    [string]$Label = "sft-gate0"
)

. "$PSScriptRoot\vultr_common.ps1"

if (-not $Plan) { $Plan = $DefaultPlan }
if (-not $Region) { $Region = $DefaultRegion }

$session = Get-VultrSession
if ($session -and $session.instance_id -and $session.ssh_host) {
    Write-Host "Session already has instance $($session.instance_id) at $($session.ssh_host) - skip provision"
    exit 0
}

Write-Host "Resolving OS + SSH key (API) ..."
$osId = Resolve-VultrGpuOsId
$sshId = Ensure-VultrSshKeyId
$userData = Get-VultrUserDataB64

$body = @{
    region     = $Region
    plan       = $Plan
    os_id      = $osId
    label      = $Label
    hostname   = $Label
    sshkey_id  = @($sshId)
    user_data  = $userData
    backups    = "disabled"
    tags       = @("sft-gate0", "ask-spurgeon")
}

Write-Host "Creating instance plan=$Plan region=$Region os_id=$osId label=$Label"
$created = Invoke-VultrApi -Method POST -Path "/instances" -Body $body
$inst = $created.instance
if (-not $inst -or -not $inst.id) {
    throw "Create instance returned no id"
}

$data = @{
    instance_id   = [string]$inst.id
    name          = $Label
    plan          = $Plan
    region        = $Region
    os_id         = $osId
    ssh_user      = "root"
    ssh_port      = 22
    ssh_host      = $(if ($inst.main_ip -and $inst.main_ip -ne "0.0.0.0") { [string]$inst.main_ip } else { $null })
    gpu_profile   = "a16"
    status        = [string]$inst.status
    created_at    = (Get-Date).ToUniversalTime().ToString("o")
    use_cpt_merge = $true
    export        = $false
    max_wall_hours = 8
}
Save-VultrSession $data
Write-Host "Provisioned instance_id=$($inst.id) status=$($inst.status)"
Write-Host "Next: .\vultr_wait_ssh.ps1"
