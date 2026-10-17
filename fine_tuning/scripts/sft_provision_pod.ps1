# Provision SFT pod: US-IL-1 + network volume 7hb931c5oe required.
# GATE-0 default checks spurgeon-qa-mix zip. Weighted Unsloth skips that (-SkipGate0Artifacts).
param(
    [ValidateSet("COMMUNITY", "SECURE")]
    [string]$CloudType = "COMMUNITY",
    [string]$PodName = "sft-gate0",
    [switch]$SkipGate0Artifacts
)

. "$PSScriptRoot\sft_runpod_common.ps1"

if (-not $SkipGate0Artifacts) {
    Test-SftArtifacts
}
else {
    foreach ($p in @(
            "fine_tuning\scripts\train_sft_sota.py",
            "fine_tuning\scripts\sft_remote_setup.sh",
            "fine_tuning\scripts\sft_remote_train_s8_weighted.sh",
            "config.py"
        )) {
        Resolve-SftArtifactPath $p | Out-Null
    }
    Write-Host "Weighted SFT artifacts OK (GATE-0 zip check skipped)"
}

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
    $podEnv = Get-SftPodEnv -PubKey $pub
    $args = @(
        "pod", "create",
        "--name", $PodName,
        "--image", $ImageNameCuda124,
        "--gpu-id", $GpuType,
        "--gpu-count", "1",
        "--data-center-ids", $DataCenter,
        "--network-volume-id", $NetworkVolumeId,
        "--volume-mount-path", "/workspace",
        "--container-disk-in-gb", "75",
        "--cloud-type", $Cloud,
        "--env", ($podEnv | ConvertTo-Json -Compress),
        "--wait",
        "--wait-timeout", "20m"
    )
    Write-Host "runpodctl pod create --name $PodName --gpu-id $GpuType --cloud-type $Cloud --network-volume-id $NetworkVolumeId (HF_TOKEN=set)"
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
    Save-SftSession @{
        pod_id = $podId
        name = $PodName
        cloud_type = $Cloud
        data_center = $DataCenter
        created_at = (Get-Date).ToString("o")
        network_volume_id = $NetworkVolumeId
        volume_mount_path = "/workspace"
        gate0_merged = $Gate0MergedRemote
        hub_v2_adapter_sha256 = $HubV2AdapterSha
        use_cpt_merge = $true
        export = $false
        max_wall_hours = 8
        auth = "runpodctl"
    }
    Write-Host "Pod created via runpodctl: $podId"
    return $true
}

# Prefer MCP OAuth REST (works when ~/.runpod/config.toml apikey is empty).
# Cloudflare blocks REST without a User-Agent — sft_provision_pod_mcp.py sets one.
$mcpScript = Join-Path $PSScriptRoot "sft_provision_pod_mcp.py"
$mcpExit = -1
if (Test-Path $mcpScript) {
    $py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $py)) { $py = "python" }
    $env:SFT_POD_NAME = $PodName
    & $py $mcpScript
    $mcpExit = $LASTEXITCODE
    if ($mcpExit -eq 0) {
        Write-Host "Provisioned via MCP OAuth REST v1"
        exit 0
    }
}

if (Invoke-RunpodctlProvision -Cloud $CloudType) { exit 0 }
if ($CloudType -eq "COMMUNITY" -and (Invoke-RunpodctlProvision -Cloud "SECURE")) { exit 0 }

# Do not fall through to bare REST when MCP already authenticated and failed
# (usually balance/stock). Bare REST only works with RUNPOD_API_KEY.
try {
    Get-RunpodApiKey | Out-Null
}
catch {
    throw ("MCP OAuth provision failed (exit=$mcpExit) and RUNPOD_API_KEY unset. " +
        "Top up RunPod balance (>= `$5 for network volume; enough for GPU rent), " +
        "or set apikey in ~/.runpod/config.toml. Last MCP errors are above.")
}

$pub = Get-SshPublicKey
$body = @{
    name = $PodName
    imageName = $ImageNameCuda124
    gpuTypeIds = @($GpuType)
    cloudType = $CloudType
    dataCenterIds = @($DataCenter)
    containerDiskInGb = 75
    volumeInGb = 0
    networkVolumeId = $NetworkVolumeId
    volumeMountPath = "/workspace"
    ports = @("22/tcp")
    supportPublicIp = $true
    env = (Get-SftPodEnv -PubKey $pub)
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

Save-SftSession @{
    pod_id = $podId
    name = $PodName
    cloud_type = $body.cloudType
    data_center = $DataCenter
    created_at = (Get-Date).ToString("o")
    network_volume_id = $NetworkVolumeId
    volume_mount_path = "/workspace"
    gate0_merged = $Gate0MergedRemote
    hub_v2_adapter_sha256 = $HubV2AdapterSha
    use_cpt_merge = $true
    export = $false
    max_wall_hours = 8
    auth = "rest_v1_apikey"
}

Write-Host "Session saved to $StateFile"
Write-Host "Next: .\sft_wait_ssh.ps1 -> .\sft_verify_mount.ps1 -> .\sft_sync_to_pod.ps1 -> .\sft_launch_train.ps1"
