# Vast CPT S7 holdout-sibling replay orchestrator.
# Default: local readiness + dry search. Does NOT rent.
# After dry + credit OK: .\vast_cpt_s7_orchestrate.ps1 -Go -StartMonitor
param(
    [switch]$Go,
    [string]$OfferId = "",
    [switch]$Pack,
    [switch]$SkipPack,
    [switch]$StartMonitor,
    [switch]$AllowLowCredit
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\vast_cpt_s7_common.ps1"

$py = Join-Path $RepoRootFromCpt ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

Write-Host "=== Vast CPT S7 holdout-sibling replay orchestrate ==="
Write-Host "go=$Go pack=$Pack start_monitor=$StartMonitor (train only if -Go)"

& $py (Join-Path $PSScriptRoot "vast_cpt_s7_local_readiness.py")
if ($LASTEXITCODE -ne 0) { throw "local readiness FAIL" }

Show-VastAccountSummary

# Dry search with S7 query/disk/label (do not call S6 vast_cpt_search — it resets S6 paths)
Write-Host "Searching Vast on-demand 4090 offers for S7 (no rent) ..."
Write-Host "Query: $SearchQuery"
$offers = Find-VastCheapestOffer -Query $SearchQuery -Limit 8
$i = 0
foreach ($o in $offers) {
    $i++
    $id = $o.id
    if (-not $id) { $id = $o.ask_contract_id }
    $dph = $o.dph_total
    if (-not $dph) { $dph = $o.dph }
    Write-Host ("{0,2}. offer_id={1}  {2:N3}/hr  gpu={3}  geo={4}" -f $i, $id, [double]$dph, $o.gpu_name, $o.geolocation)
}
if ($offers -and $offers.Count -gt 0) {
    $best = $offers[0]
    $bestId = $best.id
    if (-not $bestId) { $bestId = $best.ask_contract_id }
    Write-Host "Cheapest pick (dry): offer_id=$bestId  image=$DefaultImage  disk=${DefaultDiskGb}GB  label=$DefaultLabel"
}

$payload = Join-Path $env:VAST_LOCAL_RESULTS_DIR "payload.tar"
if ($Pack -or ($Go -and -not $SkipPack -and -not (Test-Path $payload))) {
    Write-Host "Packing S7 payload.tar ..."
    & (Join-Path $PSScriptRoot "vast_cpt_s7_pack_payload.ps1")
    if ($LASTEXITCODE -ne 0) { throw "pack failed" }
}

if (-not $Go) {
    Write-Host ""
    Write-Host "DRY COMPLETE -- no instance rented, no training started."
    Write-Host "After credit check, rent with:"
    Write-Host "  cd continued_pretrain\scripts"
    Write-Host "  .\vast_cpt_s7_orchestrate.ps1 -Go -StartMonitor"
    exit 0
}

$user = Invoke-VastaiJson -CliArgs @("show", "user")
$credit = [double]$user.credit
Write-Host ("live_credit={0:N2}" -f $credit)
if ($credit -lt 5 -and -not $AllowLowCredit) {
    throw "Vast credit $credit is under `$5. Add funds for a 3-5h 4090 run, or retry with -AllowLowCredit and a cheaper 3090 -OfferId."
}

Write-Host ""
Write-Host "GO: renting Vast GPU and launching S7 Phase B continue"
$FtScripts = Join-Path $RepoRootFromCpt "fine_tuning\scripts"
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

& (Join-Path $PSScriptRoot "vast_cpt_s7_sync.ps1")
if ($LASTEXITCODE -ne 0) { throw "sync failed" }

& (Join-Path $PSScriptRoot "vast_cpt_s7_launch.ps1")
if ($LASTEXITCODE -ne 0) { throw "launch failed" }

Write-Host "Walk-away gates to confirm in /workspace/cpt_train.log:"
Write-Host "  cpt_run_mode=continue CPT_CONTINUE_PROFILE=s7"
Write-Host "  PREV_RUN_CHECKPOINT empty / new Adam"
Write-Host "  INIT_ADAPTER SHA256 OK (ddbbee3a Phase B C-winner)"
Write-Host "  COMPOSITE_EARLY_STOP_METRICS=spurgeon,puritan,confession (no mix-val)"
Write-Host "  PIN_OK torch 2.8 + unsloth 2026.8.22"
Write-Host "  conda python under .../envs/unsloth_cpt_s7/"
Write-Host "  NOT Resuming from checkpoint-2050"

if ($StartMonitor) {
    $monPy = Join-Path $PSScriptRoot "vast_cpt_s7_monitor_until_done.py"
    $log = Join-Path $env:VAST_LOCAL_RESULTS_DIR "vast_cpt_s7_monitor.log"
    New-Item -ItemType Directory -Force -Path $env:VAST_LOCAL_RESULTS_DIR | Out-Null
    $env:CPT_TOTAL_STEPS = "955"
    $env:PYTHONIOENCODING = "utf-8"
    Write-Host "Starting S7 monitor -> $log (CPT_TOTAL_STEPS=955)"
    Start-Process -FilePath $py -ArgumentList $monPy -WorkingDirectory $PSScriptRoot -RedirectStandardOutput $log -RedirectStandardError "$log.err" -WindowStyle Hidden
    Write-Host "Monitor started. Tail $log"
}
