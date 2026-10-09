# Vast CPT S8 sweep orchestrator.
# Default: local readiness. Does not rent and does not contact Vast.
# After a later operator go: .\vast_cpt_s8_sweep_orchestrate.ps1 -Go
param(
    [switch]$Go,
    [string]$OfferId = "",
    [switch]$AllowLowCredit
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
$plan = Join-Path $PSScriptRoot "vast_cpt_s8_sweep_plan.py"

Write-Host "=== Vast CPT S8 sweep orchestrate ==="
Write-Host "go=$Go (train only if -Go)"

& $py $plan
if ($LASTEXITCODE -ne 0) { throw "local readiness FAIL" }

if (-not $Go) {
    Write-Host ""
    Write-Host "DRY COMPLETE -- no instance rented, no merge, no training started."
    Write-Host "No vastai, scp, or ssh calls were made."
    Write-Host "After operator go:"
    Write-Host "  cd continued_pretrain\scripts"
    Write-Host "  .\vast_cpt_s8_sweep_orchestrate.ps1 -Go"
    exit 0
}

# Go path. Not used by the dry readiness session.
. "$PSScriptRoot\vast_cpt_s8_sweep_common.ps1"
Show-VastAccountSummary

Write-Host "Searching Vast on-demand 4090 offers (no rent yet) ..."
$offers = Find-VastCheapestOffer -Query $SearchQuery -Limit 8
if ($offers -and $offers.Count -gt 0) {
    $best = $offers[0]
    $bestId = $best.id
    if (-not $bestId) { $bestId = $best.ask_contract_id }
    Write-Host "Cheapest pick: offer_id=$bestId  disk=${DefaultDiskGb}GB  label=$DefaultLabel"
}

Write-Host "Packing S8 payload.tar ..."
& (Join-Path $PSScriptRoot "vast_cpt_s8_sweep_pack.ps1")
if ($LASTEXITCODE -ne 0) { throw "pack failed" }

$user = Invoke-VastaiJson -CliArgs @("show", "user")
$credit = [double]$user.credit
Write-Host ("live_credit={0:N2}" -f $credit)
if ($credit -lt 5 -and -not $AllowLowCredit) {
    throw "Vast credit $credit is under `$5. Add funds, or retry with -AllowLowCredit."
}

Write-Host "GO: renting one RTX 4090 for the three-arm sweep (~5h)"
$provArgs = @{
    DiskGb = $DefaultDiskGb
    Label  = $DefaultLabel
    Force  = $true
}
if ($OfferId) { $provArgs.OfferId = $OfferId }
& (Join-Path $FtScripts "vast_provision.ps1") @provArgs
if ($LASTEXITCODE -ne 0) { throw "provision failed" }

& (Join-Path $FtScripts "vast_wait_ssh.ps1")
if ($LASTEXITCODE -ne 0) { throw "wait_ssh failed" }
& (Join-Path $FtScripts "vast_verify_gpu.ps1")
if ($LASTEXITCODE -ne 0) { throw "verify_gpu failed" }
& (Join-Path $FtScripts "vast_inject_hf_token.ps1")
if ($LASTEXITCODE -ne 0) { Write-Host "WARN: HF inject failed - continuing" }

& (Join-Path $PSScriptRoot "vast_cpt_s8_sweep_sync.ps1")
if ($LASTEXITCODE -ne 0) { throw "sync failed" }
& (Join-Path $PSScriptRoot "vast_cpt_s8_sweep_launch.ps1")
if ($LASTEXITCODE -ne 0) { throw "launch failed" }

Write-Host "Walk-away gates in /workspace/s8_launcher.log:"
Write-Host "  PIN_OK torch 2.8 + unsloth 2026.8.22"
Write-Host "  Merge complete /workspace/theology_cpt_merged_a70"
Write-Host "  ARM_START m_lo then m_hi then f_hi"
Write-Host "  PREV empty / fresh LoRA (not continue, not checkpoints_sota)"
Write-Host "  No Hub upload"
