# Vast SFT on the S8 merged CPT weights.
# Default: local readiness. Does not rent and does not contact Vast.
# -Go is refused here. Forge rents only after a later operator go.
param(
    [switch]$Go
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
$plan = Join-Path $PSScriptRoot "sft_s8_plan.py"

Write-Host "=== Vast SFT on S8 merged CPT ==="
Write-Host "go=$Go (this script never rents)"

if ($Go) {
    throw "Refusing -Go. This build is dry-ready only. Say go in Forge before any Vast rent."
}

& $py $plan
if ($LASTEXITCODE -ne 0) { throw "local readiness FAIL" }

Write-Host ""
Write-Host "DRY COMPLETE -- no instance rented, no download, no training started."
Write-Host "No vastai, scp, or ssh calls were made."
Write-Host "Base: rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit"
Write-Host "Hub LoRA v2 06354dfc stays. SFT_EXPORT=0 until F gates."
exit 0
