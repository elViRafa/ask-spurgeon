# Poll Runpod until pod SSH is reachable; writes ssh host/port to s6_session.json.
param(
    [int]$TimeoutMinutes = 20
)

$sessionFile = Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path "continued_pretrain\kaggle\runpod_cpt_v3\s6_session.json"
if (-not (Test-Path $sessionFile)) {
    throw "No session file. Run s6_provision_pod.ps1 first."
}

$env:S6_WAIT_TIMEOUT_MIN = "$TimeoutMinutes"
python (Join-Path $PSScriptRoot "s6_provision_pod_mcp.py") --wait-ssh
if ($LASTEXITCODE -ne 0) { throw "wait-ssh failed" }
