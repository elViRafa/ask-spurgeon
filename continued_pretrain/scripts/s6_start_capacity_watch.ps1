# Start s6_watch_capacity.py detached (poll 4090 every 20 min, auto-provision + train).
param(
    [int]$IntervalSec = 1200
)

$script = Join-Path $PSScriptRoot "s6_watch_capacity.py"
$logDir = Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path "continued_pretrain\kaggle\runpod_cpt_v3"
$logFile = Join-Path $logDir "s6_capacity_watch.log"
$errFile = Join-Path $logDir "s6_capacity_watch.err.log"

$env:S6_CAPACITY_INTERVAL_SEC = "$IntervalSec"

$proc = Start-Process -FilePath "python" `
    -ArgumentList "`"$script`"" `
    -WorkingDirectory $PSScriptRoot `
    -RedirectStandardOutput $logFile `
    -RedirectStandardError $errFile `
    -WindowStyle Hidden `
    -PassThru

Start-Sleep -Seconds 2
Write-Host "Capacity watcher PID $($proc.Id)"
Write-Host "Log: $logFile"
Write-Host "Polls every ${IntervalSec}s for US-IL-1 RTX 4090 + volume; auto-provisions and launches S6 continue-B."
