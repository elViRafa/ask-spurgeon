# End-to-end SFT GATE-0: provision -> verify volume -> sync -> train -> (optional) monitor.
param(
    [switch]$SkipProvision,
    [switch]$FetchOnly,
    [switch]$LaunchOnly,
    [switch]$MergeOnly,
    [switch]$StartMonitor
)

. "$PSScriptRoot\sft_runpod_common.ps1"

if ($FetchOnly) {
    & "$PSScriptRoot\sft_fetch_results.ps1"
    exit $LASTEXITCODE
}

if ($MergeOnly) {
    if (-not $SkipProvision) {
        & "$PSScriptRoot\sft_provision_pod.ps1"
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        & "$PSScriptRoot\sft_wait_ssh.ps1"
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        & "$PSScriptRoot\sft_verify_mount.ps1"
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        & "$PSScriptRoot\sft_sync_to_pod.ps1"
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    & "$PSScriptRoot\sft_launch_merge.ps1"
    exit $LASTEXITCODE
}

if (-not $LaunchOnly) {
    if (-not $SkipProvision) {
        & "$PSScriptRoot\sft_provision_pod.ps1"
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    & "$PSScriptRoot\sft_wait_ssh.ps1"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & "$PSScriptRoot\sft_verify_mount.ps1"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & "$PSScriptRoot\sft_sync_to_pod.ps1"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

& "$PSScriptRoot\sft_launch_train.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($StartMonitor) {
    & "$PSScriptRoot\sft_start_monitor.ps1"
}
exit 0
