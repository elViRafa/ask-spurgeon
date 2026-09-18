# End-to-end S6 continue-B: provision -> verify volume -> sync -> train -> (optional) monitor.
param(
    [switch]$SkipProvision,
    [switch]$FetchOnly,
    [switch]$LaunchOnly,
    [switch]$StartMonitor
)

. "$PSScriptRoot\s6_runpod_common.ps1"

if ($FetchOnly) {
    & "$PSScriptRoot\s6_fetch_results.ps1"
    exit $LASTEXITCODE
}

if (-not $LaunchOnly) {
    if (-not $SkipProvision) {
        & "$PSScriptRoot\s6_provision_pod.ps1"
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    & "$PSScriptRoot\s6_wait_ssh.ps1"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & "$PSScriptRoot\s6_verify_mount.ps1"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & "$PSScriptRoot\s6_sync_to_pod.ps1"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

& "$PSScriptRoot\s6_launch_continue_b.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($StartMonitor) {
    & "$PSScriptRoot\s6_start_monitor.ps1"
}
exit 0
