# Vast CPT S6 continue-B orchestrator.
# Default: local readiness + dry search. Does NOT rent.
# Next session: .\vast_cpt_orchestrate.ps1 -Go
param(
    [switch]$Go,
    [string]$OfferId = "",
    [switch]$Pack,
    [switch]$SkipPack,
    [switch]$StartMonitor,
    [switch]$AllowLowCredit
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\vast_cpt_common.ps1"

$py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

Write-Host "=== Vast CPT S6 orchestrate ==="
Write-Host "go=$Go pack=$Pack start_monitor=$StartMonitor (train only if -Go)"

& $py (Join-Path $PSScriptRoot "vast_cpt_local_readiness.py")
if ($LASTEXITCODE -ne 0) { throw "local readiness FAIL" }

Show-VastAccountSummary
& (Join-Path $PSScriptRoot "vast_cpt_search.ps1")
if ($LASTEXITCODE -ne 0) { throw "dry search failed" }

$payload = Join-Path $env:VAST_LOCAL_RESULTS_DIR "payload.tar"
if ($Pack -or ($Go -and -not $SkipPack -and -not (Test-Path $payload))) {
    Write-Host "Packing payload.tar on D: ..."
    & (Join-Path $PSScriptRoot "vast_cpt_pack_payload.ps1")
    if ($LASTEXITCODE -ne 0) { throw "pack failed" }
}

if (-not $Go) {
    Write-Host ""
    Write-Host "DRY COMPLETE -- no instance rented, no training started."
    Write-Host "Next session, after you say go:"
    Write-Host "  cd continued_pretrain\scripts"
    Write-Host "  .\vast_cpt_orchestrate.ps1 -Go -StartMonitor"
    Write-Host "If credit is under ~`$5, add funds for 4090 or pass a 3090 -OfferId with -AllowLowCredit"
    exit 0
}

$user = Invoke-VastaiJson -CliArgs @("show", "user")
$credit = [double]$user.credit
Write-Host ("live_credit={0:N2}" -f $credit)
if ($credit -lt 5 -and -not $AllowLowCredit) {
    throw "Vast credit $credit is under `$5. Add funds for an 8-12h 4090 run, or retry with -AllowLowCredit and a cheaper 3090 -OfferId."
}

Write-Host ""
Write-Host "GO: renting Vast GPU and launching S6 continue-B on full corpus v3"
$FtScripts = Join-Path $RepoRoot "fine_tuning\scripts"
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

& (Join-Path $PSScriptRoot "vast_cpt_sync.ps1")
if ($LASTEXITCODE -ne 0) { throw "sync failed" }

& (Join-Path $PSScriptRoot "vast_cpt_launch.ps1")
if ($LASTEXITCODE -ne 0) { throw "launch failed" }

Write-Host "Walk-away gates to confirm in /workspace/cpt_train.log:"
Write-Host "  cpt_run_mode=continue composite_stop=True"
Write-Host "  gpu_profile=ampere trainer_bf16=True"
Write-Host "  Resuming from .../checkpoint-2050"
Write-Host "  packed_epoch_steps=4128 abort_spurgeon_step=0"
Write-Host "  INIT_ADAPTER SHA256 OK"

if ($StartMonitor) {
    $monPy = Join-Path $PSScriptRoot "vast_cpt_monitor_until_done.py"
    $log = Join-Path $env:VAST_LOCAL_RESULTS_DIR "vast_cpt_monitor.log"
    New-Item -ItemType Directory -Force -Path $env:VAST_LOCAL_RESULTS_DIR | Out-Null
    Write-Host "Starting monitor -> $log"
    Start-Process -FilePath $py -ArgumentList $monPy -RedirectStandardOutput $log -RedirectStandardError "$log.err" -WindowStyle Hidden
    Write-Host "Monitor started. Tail $log"
}
