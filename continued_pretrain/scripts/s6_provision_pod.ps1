# Provision S6 continue-B pod: US-IL-1 + network volume 7hb931c5oe required.
param(
    [ValidateSet("COMMUNITY", "SECURE")]
    [string]$CloudType = "COMMUNITY",
    [string]$PodName = "s6-continue-b-cpt"
)

. "$PSScriptRoot\s6_runpod_common.ps1"

Test-S6Artifacts

function Invoke-RunpodctlProvision {
    param([string]$Cloud)
    if (-not (Test-Path $Runpodctl)) {
        return $false
    }
    try {
        Get-RunpodApiKey | Out-Null
    }
    catch {
        return $false
    }

    $pub = Get-SshPublicKey
    $args = @(
        "pod", "create",
        "--name", $PodName,
        "--image", $ImageName,
        "--gpu-id", $GpuType,
        "--gpu-count", "1",
        "--data-center-ids", $DataCenter,
        "--network-volume-id", $NetworkVolumeId,
        "--volume-mount-path", "/workspace",
        "--container-disk-in-gb", "75",
        "--cloud-type", $Cloud,
        "--env", (@{ PUBLIC_KEY = $pub } | ConvertTo-Json -Compress),
        "--wait",
        "--wait-timeout", "20m"
    )
    Write-Host "runpodctl $($args -join ' ')"
    $json = & $Runpodctl @args 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "runpodctl create failed ($Cloud): $json"
        return $false
    }
    $pod = $json | ConvertFrom-Json
    $podId = $pod.id
    if (-not $podId) { $podId = $pod.podId }
    if (-not $podId) {
        Write-Warning "runpodctl returned no pod id"
        return $false
    }
    Save-S6Session @{
        pod_id = $podId
        cloud_type = $Cloud
        data_center = $DataCenter
        created_at = (Get-Date).ToString("o")
        network_volume_id = $NetworkVolumeId
        volume_mount_path = "/workspace"
        max_wall_hours = 16
        mix_sha256 = $MixSha
        init_adapter_sha256 = $S5AdapterSha
        auth = "runpodctl"
    }
    Write-Host "Pod created via runpodctl: $podId"
    return $true
}

if (Invoke-RunpodctlProvision -Cloud $CloudType) { exit 0 }
if ($CloudType -eq "COMMUNITY" -and (Invoke-RunpodctlProvision -Cloud "SECURE")) { exit 0 }

# MCP OAuth REST v1 (same token as Cursor Runpod MCP)
$mcpScript = Join-Path $PSScriptRoot "s6_provision_pod_mcp.py"
if (Test-Path $mcpScript) {
    python $mcpScript
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Provisioned via MCP OAuth REST v1"
        exit 0
    }
}

# Direct REST v1 with RUNPOD_API_KEY
$pub = Get-SshPublicKey
$body = @{
    name = $PodName
    imageName = $ImageName
    gpuTypeIds = @($GpuType)
    cloudType = $CloudType
    dataCenterIds = @($DataCenter)
    containerDiskInGb = 75
    volumeInGb = 0
    networkVolumeId = $NetworkVolumeId
    volumeMountPath = "/workspace"
    ports = @("22/tcp")
    supportPublicIp = $true
    env = @{ PUBLIC_KEY = $pub }
    computeType = "GPU"
}

Write-Host "Creating pod ($CloudType, $DataCenter, volume $NetworkVolumeId)..."
try {
    $pod = Invoke-RunpodRestV1 -Method POST -Path "/pods" -Body $body
}
catch {
    if ($CloudType -eq "COMMUNITY") {
        Write-Warning "Community create failed; retrying SECURE cloud..."
        $body.cloudType = "SECURE"
        $pod = Invoke-RunpodRestV1 -Method POST -Path "/pods" -Body $body
    }
    else {
        throw
    }
}

$podId = $pod.id
if (-not $podId) { $podId = $pod.podId }
Write-Host "Pod created: $podId"

Save-S6Session @{
    pod_id = $podId
    cloud_type = $body.cloudType
    data_center = $DataCenter
    created_at = (Get-Date).ToString("o")
    network_volume_id = $NetworkVolumeId
    volume_mount_path = "/workspace"
    max_wall_hours = 16
    mix_sha256 = $MixSha
    init_adapter_sha256 = $S5AdapterSha
    auth = "rest_v1_apikey"
}

Write-Host "Session saved to $StateFile"
Write-Host "Next: .\s6_wait_ssh.ps1 -> .\s6_verify_mount.ps1 -> .\s6_sync_to_pod.ps1 -> .\s6_launch_continue_b.ps1"
