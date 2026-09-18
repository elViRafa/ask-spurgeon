# Shared helpers for SFT GATE-0 Runpod session (REST v1 pod create + SSH).
$ErrorActionPreference = "Stop"

$Script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Script:FtRoot = Join-Path $RepoRoot "fine_tuning"
$Script:Runpodctl = Join-Path $RepoRoot ".tools\runpodctl.exe"
$Script:SshKey = Join-Path $env:USERPROFILE ".ssh\runpod_cpt"
$Script:NetworkVolumeId = "7hb931c5oe"
$Script:DataCenter = "US-IL-1"
$Script:GpuType = "NVIDIA GeForce RTX 4090"
$Script:ImageName = "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404"
$Script:ImageNameCuda124 = "runpod/pytorch:0.7.0-cu1241-torch260-ubuntu2204"
$Script:HubV2AdapterSha = "319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478"
$Script:Gate0MergedRemote = "/workspace/theology_cpt_v2_merged_hf"
$Script:StateFile = Join-Path $FtRoot "kaggle\sft_session.json"
$Script:LocalResultsDir = Join-Path $FtRoot "kaggle\runpod_sft_gate0"

function Get-RunpodApiKey {
    if ($env:RUNPOD_API_KEY -and $env:RUNPOD_API_KEY.Trim()) {
        return $env:RUNPOD_API_KEY.Trim()
    }
    $cfg = Join-Path $env:USERPROFILE ".runpod\config.toml"
    if (Test-Path $cfg) {
        $raw = Get-Content $cfg -Raw
        if ($raw -match "apikey\s*=\s*'([^']+)'" -and $Matches[1]) {
            return $Matches[1].Trim()
        }
        if ($raw -match 'apikey\s*=\s*"([^"]+)"' -and $Matches[1]) {
            return $Matches[1].Trim()
        }
    }
    throw "RUNPOD_API_KEY not set. Export it or set apikey in $cfg (runpodctl doctor)."
}

function Get-SshPublicKey {
    $pub = "$SshKey.pub"
    if (-not (Test-Path $pub)) {
        throw "Missing SSH public key: $pub"
    }
    return (Get-Content $pub -Raw).Trim()
}

function Get-HfToken {
    if ($env:HF_TOKEN -and $env:HF_TOKEN.Trim()) {
        return $env:HF_TOKEN.Trim()
    }
    $dotenv = Join-Path $RepoRoot ".env"
    if (Test-Path $dotenv) {
        foreach ($line in Get-Content $dotenv) {
            $t = $line.Trim()
            if ($t.StartsWith("HF_TOKEN=")) {
                $v = $t.Substring("HF_TOKEN=".Length).Trim().Trim('"').Trim("'")
                if ($v) { return $v }
            }
            if ($t.StartsWith("HUGGING_FACE_HUB_TOKEN=")) {
                $v = $t.Substring("HUGGING_FACE_HUB_TOKEN=".Length).Trim().Trim('"').Trim("'")
                if ($v) { return $v }
            }
        }
    }
    throw "HF_TOKEN not set. Required to download private Hub v2 LoRA on the pod."
}

function Get-SftPodEnv {
    param([string]$PubKey)
    return @{
        PUBLIC_KEY = $PubKey
        HF_TOKEN = (Get-HfToken)
        HF_HOME = "/workspace/hf_home"
    }
}

function Save-SftSession {
    param([hashtable]$Data)
    $dir = Split-Path $StateFile -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $json = $Data | ConvertTo-Json -Depth 6
    [System.IO.File]::WriteAllText($StateFile, $json, [System.Text.UTF8Encoding]::new($false))
}

function Get-SftSession {
    if (-not (Test-Path $StateFile)) { return $null }
    return Get-Content $StateFile -Raw | ConvertFrom-Json
}

function Get-SftSshRemote {
    param($Session)
    $user = if ($Session.ssh_user) { [string]$Session.ssh_user } else { "root" }
    $hostIp = [string]$Session.ssh_host
    return "${user}@${hostIp}"
}

function Get-SftSshPort {
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

function Resolve-SftArtifactPath {
    param([string]$Relative)
    $full = Join-Path $RepoRoot $Relative
    if (Test-Path $full) { return (Resolve-Path $full).Path }
    throw "Missing artifact: $full"
}

function Test-SftArtifacts {
    $paths = @(
        "fine_tuning\data\kaggle_upload\spurgeon-qa-mix-v1.zip",
        "fine_tuning\scripts\merge_cpt_lora.py",
        "fine_tuning\scripts\train_sft_sota.py",
        "fine_tuning\scripts\eval_sft_sota.py",
        "fine_tuning\scripts\sft_remote_setup.sh",
        "fine_tuning\scripts\sft_remote_train.sh",
        "config.py"
    )
    foreach ($p in $paths) {
        Resolve-SftArtifactPath $p | Out-Null
    }
    Write-Host "SFT artifacts OK"
}
