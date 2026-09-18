# Poll Vast instance until SSH works. Writes host/port into vast_sft_session.json.
param(
    [int]$TimeoutMinutes = 25,
    [string]$InstanceId = ""
)

. "$PSScriptRoot\vast_common.ps1"

if ($InstanceId) {
    $existing = Get-VastSession
    $data = Convert-SessionToHashtable $existing
    $data.instance_id = $InstanceId.Trim()
    if (-not $data.name) { $data.name = $DefaultLabel }
    if (-not $data.gpu_profile) { $data.gpu_profile = "4090" }
    if (-not $data.max_wall_hours) { $data.max_wall_hours = $MaxWallHours }
    Save-VastSession $data
}

$session = Get-VastSession
if (-not $session -or -not $session.instance_id) {
    throw "No instance_id in vast_sft_session.json. Run vast_provision.ps1 or pass -InstanceId."
}

$id = [string]$session.instance_id
$deadline = [datetime]::UtcNow.AddMinutes($TimeoutMinutes)

while ([datetime]::UtcNow -lt $deadline) {
    try {
        $session = Update-VastSessionSshFromInstance -InstanceId $id
        Write-Host "ssh-url $($session.ssh_url)"
    }
    catch {
        Write-Host "ssh-url not ready: $($_.Exception.Message)"
    }

    $session = Get-VastSession
    if ($session.ssh_host -and $session.ssh_port) {
        $sshArgs = @(
            "-i", $SshKey,
            "-p", "$($session.ssh_port)",
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "ConnectTimeout=8",
            "-o", "BatchMode=yes"
        )
        $target = Get-VastSshRemote $session
        & ssh @($sshArgs + @($target, "mkdir -p /workspace && echo SSH_OK"))
        if ($LASTEXITCODE -eq 0) {
            $ht = Convert-SessionToHashtable $session
            $ht.status = "ssh_ready"
            Save-VastSession $ht
            Write-Host "SSH ready $target port=$($session.ssh_port)"
            exit 0
        }
        Write-Host "SSH not ready yet (${target}:$($session.ssh_port))"
    }
    Start-Sleep -Seconds 15
}

throw "SSH not ready within $TimeoutMinutes minutes for instance $id"
