# Pack the S8 sweep payload. Does not rent. Called from orchestrate -Go only.
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\vast_cpt_s8_sweep_common.ps1"

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

$loraSrc = Get-VastCptS8LoraDir
if (-not (Test-Path (Join-Path $loraSrc "adapter_model.safetensors"))) {
    throw "Missing P0 LoRA adapter at $loraSrc"
}

$mixDir = Get-VastCptS8MixDir
Copy-Tree (Join-Path $mixDir "theology_dataset") (Join-Path $stage "theology_dataset")
Copy-Tree (Join-Path $mixDir "theology_holdouts") (Join-Path $stage "theology_holdouts")
Copy-Item -Force (Join-Path $CptRoot "data\mix_v6_p0\theology_mix_manifest.json") (Join-Path $stage "theology_mix_manifest.json")
Copy-Tree $loraSrc (Join-Path $stage "theology_cpt_lora")
Copy-Item -Force (Join-Path $CptRoot "scripts\train_cpt_sota.py") (Join-Path $stage "train_cpt_sota.py")
Copy-Item -Force (Join-Path $CptRoot "scripts\eval_cpt_sota.py") (Join-Path $stage "eval_cpt_sota.py")
Copy-Item -Force (Join-Path $CptRoot "scripts\cpt_runtime.py") (Join-Path $stage "cpt_runtime.py")
Copy-Item -Force (Join-Path $CptRoot "scripts\vast_cpt_s8_sweep_plan.py") (Join-Path $stage "vast_cpt_s8_sweep_plan.py")
Copy-Item -Force (Join-Path $CptRoot "scripts\vast_cpt_s8_sweep_remote.sh") (Join-Path $stage "vast_cpt_s8_sweep_remote.sh")
Copy-Item -Force (Join-Path $RepoRootFromCpt "fine_tuning\scripts\merge_cpt_lora.py") (Join-Path $stage "merge_cpt_lora.py")

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
    "theology_dataset/dataset_dict.json",
    "theology_holdouts/spurgeon/dataset_info.json",
    "theology_cpt_lora/adapter_model.safetensors",
    "train_cpt_sota.py",
    "eval_cpt_sota.py",
    "merge_cpt_lora.py",
    "vast_cpt_s8_sweep_plan.py",
    "vast_cpt_s8_sweep_remote.sh"
)
foreach ($n in $need) {
    if ($joined -notmatch [regex]::Escape($n)) {
        throw "payload missing $n"
    }
}

$mb = [math]::Round((Get-Item $payload).Length / 1MB, 1)
Write-Host "PACK_OK payload=$payload size_mb=$mb"
Remove-Item -Recurse -Force $stage
Write-Host "Removed stage dir. Payload kept for scp."
