# Pack S7 replay payload (a_output_v6 + Phase B C-winner ddbbee3a). No checkpoints_sota. Does NOT rent.
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\vast_cpt_s7_common.ps1"

$outDir = $env:VAST_LOCAL_RESULTS_DIR
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$stage = Join-Path $outDir "stage"
$payload = Join-Path $outDir "payload.tar"

if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Force -Path $stage | Out-Null

function Copy-Tree([string]$Src, [string]$Dst) {
    if (-not (Test-Path $Src)) { throw "Missing $Src" }
    Write-Host "stage $Src -> $Dst"
    Copy-Item -Recurse -Force $Src $Dst
}

$loraSrc = Get-VastCptS7LoraDir
if (-not (Test-Path (Join-Path $loraSrc "adapter_model.safetensors"))) {
    throw "Missing flattened S7 s5best LoRA adapter at $loraSrc"
}

$mixDir = Get-VastCptS7MixDir
Copy-Tree (Join-Path $mixDir "theology_dataset") (Join-Path $stage "theology_dataset")
Copy-Tree (Join-Path $mixDir "theology_holdouts") (Join-Path $stage "theology_holdouts")
Copy-Item -Force (Join-Path $CptRoot "data\mix_v6\theology_mix_manifest.json") (Join-Path $stage "theology_mix_manifest.json")
# Flatten nested Phase B C-winner LoRA → stage/theology_cpt_lora/adapter_model.safetensors
Copy-Tree $loraSrc (Join-Path $stage "theology_cpt_lora")
Copy-Item -Force (Join-Path $CptRoot "scripts\train_cpt_sota.py") (Join-Path $stage "train_cpt_sota.py")
Copy-Item -Force (Join-Path $CptRoot "scripts\cpt_runtime.py") (Join-Path $stage "cpt_runtime.py")
Copy-Item -Force (Join-Path $CptRoot "scripts\vast_cpt_s7_remote_continue_b.sh") (Join-Path $stage "vast_cpt_s7_remote_continue_b.sh")

# Hard refuse shipping sota checkpoints
if (Test-Path (Join-Path $stage "checkpoints_sota")) {
    throw "Refuse: stage must not contain checkpoints_sota"
}

if (Test-Path $payload) { Remove-Item -Force $payload }
Write-Host "Creating $payload ..."
& tar -cf $payload -C $stage .
if ($LASTEXITCODE -ne 0) { throw "tar failed" }

$list = & tar -tf $payload
if ($LASTEXITCODE -ne 0) { throw "tar list failed" }
$joined = ($list -join "`n")
if ($joined -match "checkpoints_sota") {
    throw "Refuse: payload contains checkpoints_sota"
}
$need = @(
    "./theology_dataset/dataset_dict.json",
    "./theology_holdouts/spurgeon/dataset_info.json",
    "./theology_cpt_lora/adapter_model.safetensors",
    "./train_cpt_sota.py",
    "./vast_cpt_s7_remote_continue_b.sh"
)
foreach ($n in $need) {
    $alt = $n.TrimStart(".", "/", "\")
    if ($joined -notmatch [regex]::Escape($n) -and $joined -notmatch [regex]::Escape($alt.Replace("\", "/"))) {
        throw "payload missing $n"
    }
}

$mb = [math]::Round((Get-Item $payload).Length / 1MB, 1)
Write-Host "PACK_OK payload=$payload size_mb=$mb"
Remove-Item -Recurse -Force $stage
Write-Host "Removed stage dir. Payload kept for scp."
