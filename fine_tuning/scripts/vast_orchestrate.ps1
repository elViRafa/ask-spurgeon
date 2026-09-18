# End-to-end Vast GATE-0: search/provision -> sync -> launch -> monitor -> fetch -> destroy.
# Does NOT rent unless you run without -SkipRent (operator must say go).
param(
    [switch]$SkipRent,
    [switch]$SkipMonitor,
    [switch]$FetchOnly,
    [switch]$DestroyOnly,
    [switch]$LaunchOnly,
    [string]$InstanceId = "",
    [string]$OfferId = "",
    [int]$GpuWaitMinutes = 15,
    [int]$TimeoutMinutes = 45
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\vast_common.ps1"

function Invoke-RepoPython {
    param([string[]]$PyArgs)
    $venvPy = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    $exe = if (Test-Path $venvPy) { $venvPy } else { "python" }
    & $exe @PyArgs
    if ($LASTEXITCODE -ne 0) { throw "python failed: $($PyArgs -join ' ')" }
}

if ($DestroyOnly) {
    & "$PSScriptRoot\vast_destroy.ps1" -Force
    exit $LASTEXITCODE
}

if ($FetchOnly) {
    & "$PSScriptRoot\vast_fetch.ps1" -PartialOnly
    exit $LASTEXITCODE
}

function Invoke-DestroyOnFail {
    param([string]$Reason)
    Write-Host "FAIL: $Reason - destroying instance to stop billing"
    try { & "$PSScriptRoot\vast_destroy.ps1" -Force } catch { Write-Warning $_.Exception.Message }
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
    & "$PSScriptRoot\vast_launch.ps1"
    exit $LASTEXITCODE
}

if (-not $SkipRent) {
    if ($InstanceId) {
        & "$PSScriptRoot\vast_wait_ssh.ps1" -InstanceId $InstanceId -TimeoutMinutes $TimeoutMinutes
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    else {
        if ($OfferId) {
            & "$PSScriptRoot\vast_provision.ps1" -OfferId $OfferId
        }
        else {
            & "$PSScriptRoot\vast_provision.ps1"
        }
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        & "$PSScriptRoot\vast_wait_ssh.ps1" -TimeoutMinutes $TimeoutMinutes
        if ($LASTEXITCODE -ne 0) {
            Invoke-DestroyOnFail "SSH wait failed"
        }
    }
}
else {
    if ($InstanceId) {
        & "$PSScriptRoot\vast_wait_ssh.ps1" -InstanceId $InstanceId -TimeoutMinutes $TimeoutMinutes
    }
    else {
        & "$PSScriptRoot\vast_wait_ssh.ps1" -TimeoutMinutes $TimeoutMinutes
    }
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$gpuDeadline = [datetime]::UtcNow.AddMinutes($GpuWaitMinutes)
$gpuOk = $false
while ([datetime]::UtcNow -lt $gpuDeadline) {
    & "$PSScriptRoot\vast_verify_gpu.ps1"
    if ($LASTEXITCODE -eq 0) { $gpuOk = $true; break }
    Write-Host "Waiting for nvidia-smi ..."
    Start-Sleep -Seconds 20
}
if (-not $gpuOk) {
    Invoke-DestroyOnFail "nvidia-smi never became ready"
}

& "$PSScriptRoot\vast_sync.ps1"
if ($LASTEXITCODE -ne 0) { Invoke-DestroyOnFail "sync failed" }

& "$PSScriptRoot\vast_inject_hf_token.ps1"
if ($LASTEXITCODE -ne 0) { Invoke-DestroyOnFail "HF token inject failed" }

& "$PSScriptRoot\vast_launch.ps1"
if ($LASTEXITCODE -ne 0) { Invoke-DestroyOnFail "launch failed" }

if ($SkipMonitor) {
    Write-Host "Launched. Run: python fine_tuning\scripts\vast_monitor_until_done.py"
    exit 0
}

$venvPy = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$exe = if (Test-Path $venvPy) { $venvPy } else { "python" }
& $exe (Join-Path $PSScriptRoot "vast_monitor_until_done.py")
exit $LASTEXITCODE
