# Shared helpers for S6 continue-B Runpod session (REST v1 pod create + SSH).
$ErrorActionPreference = "Stop"

$Script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Script:CptRoot = Join-Path $RepoRoot "continued_pretrain"
$Script:Runpodctl = Join-Path $RepoRoot ".tools\runpodctl.exe"
$Script:SshKey = Join-Path $env:USERPROFILE ".ssh\runpod_cpt"
$Script:NetworkVolumeId = "7hb931c5oe"
$Script:DataCenter = "US-IL-1"
$Script:GpuType = "NVIDIA GeForce RTX 4090"
$Script:ImageName = "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404"
$Script:ImageNameCuda124 = "runpod/pytorch:0.7.0-cu1241-torch260-ubuntu2204"
$Script:MinCudaVersion = "12.8"
$Script:S5AdapterSha = "ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303"
$Script:MixSha = "23dd3820baa0b657cb6528e4fdf1b2d4813c3cfa7b7c982805b4a7ff34990973"
$Script:StateFile = Join-Path $CptRoot "kaggle\runpod_cpt_v3\s6_session.json"

function Get-RunpodApiKey {
    function Test-NonEmptyKey([string]$Candidate) {
        if (-not $Candidate) { return $null }
        $t = $Candidate.Trim().Trim("'").Trim('"')
        if (-not $t -or $t -eq "''" -or $t -eq '""') { return $null }
        return $t
    }
    $fromEnv = Test-NonEmptyKey $env:RUNPOD_API_KEY
    if ($fromEnv) { return $fromEnv }
    $cfg = Join-Path $env:USERPROFILE ".runpod\config.toml"
    if (Test-Path $cfg) {
        $raw = Get-Content $cfg -Raw
        if ($raw -match "apikey\s*=\s*'([^']*)'" -and $Matches[1]) {
            $k = Test-NonEmptyKey $Matches[1]
            if ($k) { return $k }
        }
        if ($raw -match 'apikey\s*=\s*"([^"]*)"' -and $Matches[1]) {
            $k = Test-NonEmptyKey $Matches[1]
            if ($k) { return $k }
        }
        # runpodctl often writes unquoted: apikey = rpa_...
        if ($raw -match '(?m)^\s*apikey\s*=\s*([^\s#]+)\s*$' -and $Matches[1]) {
            $k = Test-NonEmptyKey $Matches[1]
            if ($k) { return $k }
        }
    }
    throw "RUNPOD_API_KEY not set (or empty in $cfg). Export a real key or run flash login / runpodctl doctor."
}

function Get-SshPublicKey {
    $pub = "$SshKey.pub"
    if (-not (Test-Path $pub)) {
        throw "Missing SSH public key: $pub"
    }
    return (Get-Content $pub -Raw).Trim()
}

function Save-S6Session {
    param([hashtable]$Data)
    $dir = Split-Path $StateFile -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    ($Data | ConvertTo-Json -Depth 6) | Set-Content -Path $StateFile -Encoding UTF8
}

function Get-S6Session {
    if (-not (Test-Path $StateFile)) { return $null }
    return Get-Content $StateFile -Raw | ConvertFrom-Json
}

function Get-S6SshRemote {
    param($Session)
    $user = if ($Session.ssh_user) { [string]$Session.ssh_user } else { "root" }
    $hostIp = [string]$Session.ssh_host
    return "${user}@${hostIp}"
}

function Get-S6SshPort {
    param($Session)
    if ($Session.ssh_port) { return [int]$Session.ssh_port }
    return 22
}

function Invoke-RunpodRestV1 {
    param(
        [string]$Method,
        [string]$Path,
        [object]$Body = $null
    )
    $key = Get-RunpodApiKey
    $uri = "https://rest.runpod.io/v1$Path"
    $headers = @{
        Authorization = "Bearer $key"
        "Content-Type" = "application/json"
    }
    if ($null -eq $Body) {
        return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers
    }
    $json = $Body | ConvertTo-Json -Depth 8 -Compress
    return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers -Body $json
}

function Resolve-ArtifactPath {
    param([string]$Relative)
    $full = Join-Path $CptRoot $Relative
    if (Test-Path $full) { return (Resolve-Path $full).Path }
    throw "Missing artifact: $full"
}

function Test-S6Artifacts {
    $paths = @(
        "kaggle\a_output_v3\theology_dataset\dataset_dict.json",
        "kaggle\a_output_v3\theology_holdouts\spurgeon\dataset_info.json",
        "data\theology_mix_manifest.json",
        "kaggle\runpod_cpt_v3\theology_cpt_lora\adapter_config.json",
        "kaggle\runpod_cpt_v3\theology_cpt_lora\adapter_model.safetensors",
        "scripts\train_cpt_sota.py",
        "scripts\cpt_runtime.py"
    )
    foreach ($p in $paths) {
        Resolve-ArtifactPath $p | Out-Null
    }
    Write-Host "S6 artifacts OK"
}
