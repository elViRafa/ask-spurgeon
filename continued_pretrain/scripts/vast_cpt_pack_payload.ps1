# Pack full-corpus S6 payload on D: for a single Vast scp. Does NOT rent or train.
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\vast_cpt_common.ps1"

$outDir = $env:VAST_LOCAL_RESULTS_DIR
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$stage = Join-Path $outDir "stage"
$payload = Join-Path $outDir "payload.tar"

if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Force -Path $stage | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $stage "checkpoints_sota") | Out-Null

function Copy-Tree([string]$Src, [string]$Dst) {
    if (-not (Test-Path $Src)) { throw "Missing $Src" }
    Write-Host "stage $Src -> $Dst"
    Copy-Item -Recurse -Force $Src $Dst
}

Copy-Tree (Join-Path $CptRoot "kaggle\a_output_v3\theology_dataset") (Join-Path $stage "theology_dataset")
Copy-Tree (Join-Path $CptRoot "kaggle\a_output_v3\theology_holdouts") (Join-Path $stage "theology_holdouts")
Copy-Item -Force (Join-Path $CptRoot "data\theology_mix_manifest.json") (Join-Path $stage "theology_mix_manifest.json")
Copy-Tree (Join-Path $CptRoot "kaggle\runpod_cpt_v3\theology_cpt_lora") (Join-Path $stage "theology_cpt_lora")
Copy-Tree (Get-VastCptResumeCkpt) (Join-Path $stage "checkpoints_sota\checkpoint-2050")
Copy-Item -Force (Join-Path $CptRoot "scripts\train_cpt_sota.py") (Join-Path $stage "train_cpt_sota.py")
Copy-Item -Force (Join-Path $CptRoot "scripts\cpt_runtime.py") (Join-Path $stage "cpt_runtime.py")
Copy-Item -Force (Join-Path $CptRoot "scripts\vast_cpt_remote_continue_b.sh") (Join-Path $stage "vast_cpt_remote_continue_b.sh")

if (Test-Path $payload) { Remove-Item -Force $payload }
Write-Host "Creating $payload ..."
& tar -cf $payload -C $stage .
if ($LASTEXITCODE -ne 0) { throw "tar failed" }

$list = & tar -tf $payload
if ($LASTEXITCODE -ne 0) { throw "tar list failed" }
$need = @(
    "./theology_dataset/dataset_dict.json",
    "./theology_holdouts/spurgeon/dataset_info.json",
    "./theology_cpt_lora/adapter_model.safetensors",
    "./checkpoints_sota/checkpoint-2050/trainer_state.json",
    "./train_cpt_sota.py",
    "./vast_cpt_remote_continue_b.sh"
)
# bsdtar may omit ./ prefix
$joined = ($list -join "`n")
foreach ($n in $need) {
    $alt = $n.TrimStart(".", "/", "\")
    if ($joined -notmatch [regex]::Escape($n) -and $joined -notmatch [regex]::Escape($alt.Replace("\", "/"))) {
        throw "payload missing $n"
    }
}

$mb = [math]::Round((Get-Item $payload).Length / 1MB, 1)
Write-Host "PACK_OK payload=$payload size_mb=$mb"
Remove-Item -Recurse -Force $stage
Write-Host "Removed stage dir. Payload kept for next-session scp."
