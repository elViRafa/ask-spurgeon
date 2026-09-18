# Verify the pod has network volume 7hb931c5oe mounted at /workspace.
. "$PSScriptRoot\sft_runpod_common.ps1"

$session = Get-SftSession
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready - run sft_wait_ssh.ps1 first"
}

$port = Get-SftSshPort $session
$sshTarget = Get-SftSshRemote $session
$sshArgs = @("-i", $SshKey, "-p", "$port", "-o", "StrictHostKeyChecking=accept-new")

& ssh @($sshArgs + @($sshTarget, "df -h /workspace"))
if ($LASTEXITCODE -ne 0) { throw "SSH verify failed" }

$volId = [string]$session.network_volume_id
if (-not $volId -or $volId -eq "null") {
    throw @"
ABORT: Pod has no network_volume_id in sft_session.json.
Delete this pod and re-provision with volume $NetworkVolumeId (US-IL-1) mounted at /workspace.
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
