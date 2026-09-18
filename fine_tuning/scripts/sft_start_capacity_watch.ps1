# Start sft_watch_capacity.py detached (poll 4090, auto-provision + SFT GATE-0).
param(
    [int]$IntervalSec = 600
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$script = Join-Path $PSScriptRoot "sft_watch_capacity.py"
$logDir = Join-Path $repoRoot "fine_tuning\kaggle"
$logFile = Join-Path $logDir "sft_capacity_watch.log"
$errFile = Join-Path $logDir "sft_capacity_watch.err.log"
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }

$env:SFT_CAPACITY_INTERVAL_SEC = "$IntervalSec"

$proc = Start-Process -FilePath $python `
    -ArgumentList "`"$script`"" `
    -WorkingDirectory $PSScriptRoot `
    -RedirectStandardOutput $logFile `
    -RedirectStandardError $errFile `
    -WindowStyle Hidden `
    -PassThru

Start-Sleep -Seconds 2
Write-Host "SFT capacity watcher PID $($proc.Id)"
Write-Host "Log: $logFile"
Write-Host "Polls every ${IntervalSec}s for US-IL-1 4090/L40S + volume; deletes idle pods; saves artifacts locally."
