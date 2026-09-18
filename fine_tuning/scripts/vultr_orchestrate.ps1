# End-to-end Vultr GATE-0: probe API -> provision -> sync -> launch -> monitor -> fetch -> destroy.
param(
    [switch]$SkipProvision,
    [switch]$SkipMonitor,
    [switch]$FetchOnly,
    [switch]$DestroyOnly,
    [switch]$LaunchOnly,
    [string]$SshHost = "",
    [int]$ApiWaitMinutes = 20,
    [int]$GpuWaitMinutes = 15
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\vultr_common.ps1"

function Invoke-RepoPython {
    param([string[]]$PyArgs)
    $venvPy = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    $exe = if (Test-Path $venvPy) { $venvPy } else { "python" }
    & $exe @PyArgs
    if ($LASTEXITCODE -ne 0) { throw "python failed: $($PyArgs -join ' ')" }
}

if ($DestroyOnly) {
    & "$PSScriptRoot\vultr_destroy.ps1" -Force
    exit $LASTEXITCODE
}

if ($FetchOnly) {
    & "$PSScriptRoot\vultr_fetch.ps1" -PartialOnly
    exit $LASTEXITCODE
}

function Invoke-DestroyOnFail {
    param([string]$Reason)
    Write-Host "FAIL: $Reason - destroying instance to stop billing"
    try { & "$PSScriptRoot\vultr_destroy.ps1" -Force } catch { Write-Warning $_.Exception.Message }
    throw $Reason
}

$zip = Join-Path $RepoRoot "fine_tuning\data\kaggle_upload\spurgeon-qa-mix-v1.zip"
$train = Join-Path $RepoRoot "fine_tuning\data\qa_mix_train.jsonl"
if ((Test-Path $zip) -and (Test-Path $train) -and ((Get-Item $train).LastWriteTimeUtc -gt (Get-Item $zip).LastWriteTimeUtc.AddSeconds(1))) {
    Write-Host "QA mix zip stale vs train - repacking"
    Invoke-RepoPython @((Join-Path $RepoRoot "fine_tuning\scripts\12_package_kaggle_qa_mix.py"))
}

Write-Host "Local GATE-0 readiness"
Invoke-RepoPython @((Join-Path $RepoRoot "fine_tuning\scripts\13_sft_local_readiness.py"), "--gate0")

if ($LaunchOnly) {
    & "$PSScriptRoot\vultr_launch.ps1"
    exit $LASTEXITCODE
}

if (-not $SkipProvision) {
    if ($SshHost) {
        & "$PSScriptRoot\vultr_wait_ssh.ps1" -SshHost $SshHost
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    else {
        Write-Host "Probing Vultr API (wait up to ${ApiWaitMinutes} min for IP allowlist) ..."
        & "$PSScriptRoot\vultr_probe_api.ps1" -TimeoutMinutes $ApiWaitMinutes -IntervalSec 30
        if ($LASTEXITCODE -ne 0) {
            throw "Vultr API blocked. Allowlist the agent IP, or re-run with -SshHost <ip> after creating the GPU VM in the console."
        }
        & "$PSScriptRoot\vultr_provision.ps1"
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        & "$PSScriptRoot\vultr_wait_ssh.ps1"
        if ($LASTEXITCODE -ne 0) {
            Invoke-DestroyOnFail "SSH wait failed"
        }
    }
}
else {
    & "$PSScriptRoot\vultr_wait_ssh.ps1"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$gpuDeadline = [datetime]::UtcNow.AddMinutes($GpuWaitMinutes)
$gpuOk = $false
while ([datetime]::UtcNow -lt $gpuDeadline) {
    & "$PSScriptRoot\vultr_verify_gpu.ps1"
    if ($LASTEXITCODE -eq 0) { $gpuOk = $true; break }
    Write-Host "Waiting for nvidia-smi ..."
    Start-Sleep -Seconds 20
}
if (-not $gpuOk) {
    Invoke-DestroyOnFail "nvidia-smi never became ready"
}

& "$PSScriptRoot\vultr_sync.ps1"
if ($LASTEXITCODE -ne 0) { Invoke-DestroyOnFail "sync failed" }

& "$PSScriptRoot\vultr_inject_hf_token.ps1"
if ($LASTEXITCODE -ne 0) { Invoke-DestroyOnFail "HF token inject failed" }

& "$PSScriptRoot\vultr_launch.ps1"
if ($LASTEXITCODE -ne 0) { Invoke-DestroyOnFail "launch failed" }

if ($SkipMonitor) {
    Write-Host "Launched. Run: python fine_tuning\scripts\vultr_monitor_until_done.py"
    exit 0
}

$venvPy = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$exe = if (Test-Path $venvPy) { $venvPy } else { "python" }
& $exe (Join-Path $PSScriptRoot "vultr_monitor_until_done.py")
exit $LASTEXITCODE
