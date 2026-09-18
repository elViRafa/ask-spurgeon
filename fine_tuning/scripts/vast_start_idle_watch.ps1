# Start / restart the 15-minute Vast idle+SFT monitor (destroys unused GPU).
param(
    [switch]$KillExisting
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Monitor = Join-Path $PSScriptRoot "vast_monitor_until_done.py"
$LogDir = Join-Path $RepoRoot "fine_tuning\kaggle\vast_sft_gate0"
$Log = Join-Path $LogDir "vast_monitor.log"
$ErrLog = Join-Path $LogDir "vast_monitor.err.log"
$venvPy = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$exe = if (Test-Path $venvPy) { $venvPy } else { "python" }

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
}

$existing = Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='python3.13.exe' OR Name='python3.14.exe'" |
    Where-Object { $_.CommandLine -and $_.CommandLine -match "vast_monitor_until_done" }

if ($existing) {
    if ($KillExisting) {
        foreach ($p in $existing) {
            Write-Host "Stopping old monitor PID $($p.ProcessId)"
            Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
    }
    else {
        Write-Host "Monitor already running (PID(s): $($existing.ProcessId -join ', ')). Use -KillExisting to restart."
        exit 0
    }
}

$env:VAST_MONITOR_INTERVAL_SEC = if ($env:VAST_MONITOR_INTERVAL_SEC) { $env:VAST_MONITOR_INTERVAL_SEC } else { "900" }
$env:VAST_IDLE_STREAK_LIMIT = if ($env:VAST_IDLE_STREAK_LIMIT) { $env:VAST_IDLE_STREAK_LIMIT } else { "2" }
$env:PYTHONIOENCODING = "utf-8"

Write-Host "Starting monitor interval=$($env:VAST_MONITOR_INTERVAL_SEC)s idle_streak=$($env:VAST_IDLE_STREAK_LIMIT) log=$Log"
$argList = @("-u", $Monitor)
Start-Process -FilePath $exe -ArgumentList $argList -WorkingDirectory $PSScriptRoot `
    -RedirectStandardOutput $Log -RedirectStandardError $ErrLog -WindowStyle Hidden
Write-Host "Monitor launched. Tail: Get-Content '$Log' -Wait -Tail 30"
