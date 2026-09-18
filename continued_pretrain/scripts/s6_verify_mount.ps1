# Verify the pod has network volume 7hb931c5oe mounted at /workspace (abort if container-only disk).
. "$PSScriptRoot\s6_runpod_common.ps1"

$session = Get-S6Session
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready - run s6_wait_ssh.ps1 first"
}

$port = Get-S6SshPort $session
$sshTarget = Get-S6SshRemote $session
$sshArgs = @("-i", $SshKey, "-p", "$port", "-o", "StrictHostKeyChecking=accept-new")

& ssh @($sshArgs + @($sshTarget, "df -h /workspace"))
if ($LASTEXITCODE -ne 0) { throw "SSH verify failed" }

$volId = [string]$session.network_volume_id
if (-not $volId -or $volId -eq "null") {
    throw @"
ABORT: Pod has no network_volume_id in s6_session.json.
Delete this pod and re-provision with volume $NetworkVolumeId (US-IL-1) mounted at /workspace.
Training on container disk alone loses all checkpoints when the pod is deleted.
"@
}

Write-Host "Session reports network volume: $volId (expected $NetworkVolumeId)"
if ($volId -ne $NetworkVolumeId) {
    Write-Warning "Volume id mismatch - confirm in Runpod console before training."
}

$dfLine = & ssh @($sshArgs + @($sshTarget, "df -h /workspace | tail -1"))
if ($dfLine -notmatch "runpod|mfs#") {
    throw "ABORT: /workspace does not look like a Runpod network volume mount: $dfLine"
}

Write-Host "Mount check OK - safe to sync and train."
