# Start sft_monitor_until_done.py detached.
param(
    [int]$IntervalSec = 900,
    [double]$MaxWallHours = 8
)

$script = Join-Path $PSScriptRoot "sft_monitor_until_done.py"
$logDir = Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path "fine_tuning\kaggle"
$logFile = Join-Path $logDir "sft_monitor.log"

$env:SFT_MONITOR_INTERVAL_SEC = "$IntervalSec"
$env:SFT_MAX_WALL_HOURS = "$MaxWallHours"

$proc = Start-Process -FilePath "python" `
    -ArgumentList "`"$script`"" `
    -WorkingDirectory $PSScriptRoot `
    -RedirectStandardOutput $logFile `
    -RedirectStandardError (Join-Path $logDir "sft_monitor.err.log") `
    -WindowStyle Hidden `
    -PassThru

Start-Sleep -Seconds 1
Write-Host "Monitor PID $($proc.Id)"
Write-Host "Log: $logFile"
Write-Host "Poll every ${IntervalSec}s; syncs checkpoints each poll."
Write-Host "Deletes pod when SFT finishes OR after ${MaxWallHours}h wall."
