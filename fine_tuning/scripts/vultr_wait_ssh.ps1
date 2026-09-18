# Poll Vultr instance until SSH works. Writes ssh_host into vultr_sft_session.json.
param(
    [int]$TimeoutMinutes = 25,
    [string]$SshHost = ""
)

. "$PSScriptRoot\vultr_common.ps1"

if ($SshHost) {
    $existing = Get-VultrSession
    $data = @{}
    if ($existing) {
        $existing.PSObject.Properties | ForEach-Object { $data[$_.Name] = $_.Value }
    }
    $data.ssh_host = $SshHost.Trim()
    $data.ssh_user = "root"
    $data.ssh_port = 22
    if (-not $data.name) { $data.name = "sft-gate0-attach" }
    Save-VultrSession $data
}

$session = Get-VultrSession
if (-not $session) {
    throw "No vultr_sft_session.json. Run vultr_provision.ps1 or pass -SshHost."
}

$deadline = [datetime]::UtcNow.AddMinutes($TimeoutMinutes)
$sshArgsBase = @(
    "-i", $SshKey,
    "-p", "22",
    "-o", "StrictHostKeyChecking=accept-new",
    "-o", "ConnectTimeout=8",
    "-o", "BatchMode=yes"
)

while ([datetime]::UtcNow -lt $deadline) {
    if ($session.instance_id) {
        try {
            $got = Invoke-VultrApi -Method GET -Path "/instances/$($session.instance_id)"
            $inst = $got.instance
            $ip = [string]$inst.main_ip
            if ($ip -and $ip -ne "0.0.0.0") {
                $ht = @{}
                $session.PSObject.Properties | ForEach-Object { $ht[$_.Name] = $_.Value }
                $ht.ssh_host = $ip
                $ht.status = [string]$inst.status
                $ht.power_status = [string]$inst.power_status
                Save-VultrSession $ht
                $session = Get-VultrSession
            }
            Write-Host "instance status=$($inst.status) power=$($inst.power_status) ip=$ip"
        }
        catch {
            Write-Host "GET instance: $($_.Exception.Message)"
        }
    }

    if ($session.ssh_host) {
        $target = Get-VultrSshRemote $session
        & ssh @($sshArgsBase + @($target, "mkdir -p /workspace && echo SSH_OK"))
        if ($LASTEXITCODE -eq 0) {
            Write-Host "SSH ready $target"
            exit 0
        }
        Write-Host "SSH not ready yet"
    }
    Start-Sleep -Seconds 15
}

throw "SSH not ready within $TimeoutMinutes minutes"
