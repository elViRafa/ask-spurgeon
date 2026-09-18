# Dry-search Vast 4090 offers for CPT S6. Does NOT rent.
param(
    [int]$Limit = 8
)

$ErrorActionPreference = "Stop"
$CptRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$env:VAST_SESSION_FILE = Join-Path $CptRoot "kaggle\runpod_cpt_v3\vast_cpt_session.json"
$env:VAST_LOCAL_RESULTS_DIR = Join-Path $CptRoot "kaggle\runpod_cpt_v3\vast_cpt_s6"

. (Join-Path $PSScriptRoot "vast_cpt_common.ps1")

Write-Host "Searching Vast on-demand 4090 offers for CPT (no rent) ..."
Write-Host "Query: $SearchQuery"
$offers = Find-VastCheapestOffer -Query $SearchQuery -Limit $Limit

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
    $frac = $o.gpu_frac
    Write-Host ("{0,2}. offer_id={1}  {2:N3}/hr  gpu={3}  frac={4}  rel={5}  disk={6}GB  geo={7}" -f $i, $id, [double]$dph, $gpu, $frac, $rel, $disk, $geo)
}

$best = $offers[0]
$bestId = $best.id
if (-not $bestId) { $bestId = $best.ask_contract_id }
Write-Host ""
Write-Host "Cheapest pick (dry): offer_id=$bestId  image=$DefaultImage  disk=${DefaultDiskGb}GB  label=$DefaultLabel"
Write-Host "This script does NOT rent. Next session: .\vast_cpt_orchestrate.ps1 -Go"
