# Rent a Vast on-demand RTX 4090 for GATE-0 merge + SFT. Does not sync/train.
param(
    [string]$OfferId = "",
    [string]$Image = "",
    [int]$DiskGb = 0,
    [string]$Label = "",
    [switch]$Force
)

. "$PSScriptRoot\vast_common.ps1"

if (-not $Image) { $Image = $DefaultImage }
if ($DiskGb -le 0) { $DiskGb = $DefaultDiskGb }
if (-not $Label) { $Label = $DefaultLabel }

$session = Get-VastSession
if ($session -and $session.instance_id -and $session.ssh_host -and -not $Force) {
    Write-Host "Session already has instance $($session.instance_id) at $($session.ssh_host):$($session.ssh_port) - skip provision"
    exit 0
}

if (-not $OfferId) {
    Write-Host "Picking cheapest on-demand 4090 offer ..."
    $offers = Find-VastCheapestOffer -Limit 3
    $best = $offers[0]
    $OfferId = [string]$best.id
    if (-not $OfferId) { $OfferId = [string]$best.ask_contract_id }
    $dph = $best.dph_total
    if (-not $dph) { $dph = $best.dph }
    Write-Host "Selected offer_id=$OfferId dph=$dph gpu=$($best.gpu_name)"
}

# Light bootstrap for nvidia/cuda images (setup.sh also ensures unzip + py3.11).
$onstart = "mkdir -p /workspace; export DEBIAN_FRONTEND=noninteractive; (apt-get update -qq && apt-get install -y -qq unzip python3.11 python3.11-venv python3.11-dev) || true; echo VAST_ONSTART_OK"
Write-Host "Creating instance offer=$OfferId image=$Image disk=${DiskGb}GB label=$Label"
$created = Invoke-VastaiJson -CliArgs @(
    "create", "instance", "$OfferId",
    "--image", $Image,
    "--disk", "$DiskGb",
    "--ssh",
    "--direct",
    "--label", $Label,
    "--onstart-cmd", $onstart
)

$newId = $null
if ($created.new_contract) { $newId = [string]$created.new_contract }
elseif ($created.instance_id) { $newId = [string]$created.instance_id }
elseif ($created.id) { $newId = [string]$created.id }
if (-not $newId) {
    throw "create instance returned no contract/id: $($created | ConvertTo-Json -Compress)"
}

$data = @{
    instance_id    = $newId
    offer_id       = $OfferId
    name           = $Label
    image          = $Image
    disk_gb        = $DiskGb
    ssh_user       = "root"
    ssh_port       = $null
    ssh_host       = $null
    gpu_profile    = "4090"
    status         = "creating"
    created_at     = (Get-Date).ToUniversalTime().ToString("o")
    use_cpt_merge  = $true
    export         = $false
    max_wall_hours = $MaxWallHours
}
Save-VastSession $data
Write-Host "Provisioned instance_id=$newId"
Write-Host "Next: .\vast_wait_ssh.ps1"
