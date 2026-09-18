# Poll Runpod until pod SSH is reachable; writes ssh host/port to sft_session.json.
param(
    [int]$TimeoutMinutes = 20
)

$sessionFile = Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path "fine_tuning\kaggle\sft_session.json"
if (-not (Test-Path $sessionFile)) {
    throw "No session file. Run sft_provision_pod.ps1 first."
}

$env:SFT_WAIT_TIMEOUT_MIN = "$TimeoutMinutes"
python (Join-Path $PSScriptRoot "sft_provision_pod_mcp.py") --wait-ssh
if ($LASTEXITCODE -ne 0) { throw "wait-ssh failed" }
