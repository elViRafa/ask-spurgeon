# Dry search for GATE-0 RTX 4090 offers. Does NOT rent.
param(
    [string]$Query = "",
    [int]$Limit = 8
)

. "$PSScriptRoot\vast_common.ps1"

if (-not $Query) { $Query = $SearchQuery }

Write-Host "Searching Vast on-demand offers (no rent) ..."
Write-Host "Query: $Query"
$offers = Find-VastCheapestOffer -Query $Query -Limit $Limit

$i = 0
foreach ($o in $offers) {
    $i++
    $id = $o.id
    if (-not $id) { $id = $o.ask_contract_id }
    $dph = $o.dph_total
    if (-not $dph) { $dph = $o.dph }
    $gpu = $o.gpu_name
    $rel = $o.reliability
    if (-not $rel) { $rel = $o.reliability2 }
    $disk = $o.disk_space
    $geo = $o.geolocation
    Write-Host ("{0,2}. offer_id={1}  {2:N3}/hr  gpu={3}  rel={4}  disk={5}GB  geo={6}" -f $i, $id, [double]$dph, $gpu, $rel, $disk, $geo)
}

$best = $offers[0]
$bestId = $best.id
if (-not $bestId) { $bestId = $best.ask_contract_id }
Write-Host ""
Write-Host "Cheapest pick (dry): offer_id=$bestId  image=$DefaultImage  disk=${DefaultDiskGb}GB"
Write-Host "To rent: .\vast_provision.ps1   (only when operator says go)"
