# Poll Runpod until pod SSH is reachable; writes ssh host/port to session JSON.
param(
    [int]$TimeoutMinutes = 20
)

. "$PSScriptRoot\sft_runpod_common.ps1"

$sessionFile = $StateFile
if (-not (Test-Path $sessionFile)) {
    throw "No session file at $sessionFile. Run provision first (or set SFT_SESSION_FILE)."
}

$env:SFT_WAIT_TIMEOUT_MIN = "$TimeoutMinutes"
$env:SFT_SESSION_FILE = $sessionFile
python (Join-Path $PSScriptRoot "sft_provision_pod_mcp.py") --wait-ssh
if ($LASTEXITCODE -ne 0) { throw "wait-ssh failed" }
