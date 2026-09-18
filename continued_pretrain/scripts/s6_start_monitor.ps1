# Start s6_monitor_until_done.py detached; logs to kaggle/runpod_cpt_v3/s6_monitor.log
param(
    [int]$IntervalSec = 900,
    [double]$MaxWallHours = 16
)

$script = Join-Path $PSScriptRoot "s6_monitor_until_done.py"
$logDir = Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path "continued_pretrain\kaggle\runpod_cpt_v3"
$logFile = Join-Path $logDir "s6_monitor.log"

$env:S6_MONITOR_INTERVAL_SEC = "$IntervalSec"
$env:S6_MAX_WALL_HOURS = "$MaxWallHours"

$proc = Start-Process -FilePath "python" `
    -ArgumentList "`"$script`"" `
    -WorkingDirectory $PSScriptRoot `
    -RedirectStandardOutput $logFile `
    -RedirectStandardError (Join-Path $logDir "s6_monitor.err.log") `
    -WindowStyle Hidden `
    -PassThru

Start-Sleep -Seconds 1
Write-Host "Monitor PID $($proc.Id)"
Write-Host "Log: $logFile"
Write-Host "Poll every ${IntervalSec}s; syncs complete checkpoints each poll."
Write-Host "Deletes pod when B finishes OR after ${MaxWallHours}h wall (billing backstop)."
