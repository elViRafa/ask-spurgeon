# Shared helpers for Vultr GATE-0 SFT (REST v2 + SSH). Never print VULTR_API_KEY / HF_TOKEN.
$ErrorActionPreference = "Stop"

$Script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Script:FtRoot = Join-Path $RepoRoot "fine_tuning"
$Script:SshKey = Join-Path $env:USERPROFILE ".ssh\runpod_cpt"
$Script:HubV2AdapterSha = "319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478"
$Script:Gate0MergedRemote = "/workspace/theology_cpt_v2_merged_hf"
$Script:StateFile = Join-Path $FtRoot "kaggle\vultr_sft_session.json"
$Script:LocalResultsDir = Join-Path $FtRoot "kaggle\vultr_sft_gate0"
$Script:VultrApiBase = "https://api.vultr.com/v2"
$Script:DefaultPlan = "vcg-a16-12c-128g-32vram"
$Script:DefaultRegion = "blr"
$Script:DefaultOsId = 2284
$Script:SshKeyName = "search-sermons-sft"

function Get-VultrApiKey {
    if ($env:VULTR_API_KEY -and $env:VULTR_API_KEY.Trim()) {
        return $env:VULTR_API_KEY.Trim()
    }
    $dotenv = Join-Path $RepoRoot ".env"
    if (Test-Path $dotenv) {
        foreach ($line in Get-Content $dotenv) {
            $t = $line.Trim()
            if ($t.StartsWith("VULTR_API_KEY=")) {
                $v = $t.Substring("VULTR_API_KEY=".Length).Trim().Trim('"').Trim("'")
                if ($v) { return $v }
            }
        }
    }
    throw "VULTR_API_KEY not set. Add it to .env (never commit) or export it."
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
    throw "HF_TOKEN not set. Required to download private Hub v2 LoRA."
}

function Save-VultrSession {
    param([hashtable]$Data)
    $dir = Split-Path $StateFile -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $json = $Data | ConvertTo-Json -Depth 6
    [System.IO.File]::WriteAllText($StateFile, $json, [System.Text.UTF8Encoding]::new($false))
}

function Get-VultrSession {
    if (-not (Test-Path $StateFile)) { return $null }
    return Get-Content $StateFile -Raw -Encoding utf8 | ConvertFrom-Json
}

function Get-VultrSshRemote {
    param($Session)
    $user = if ($Session.ssh_user) { [string]$Session.ssh_user } else { "root" }
    $hostIp = [string]$Session.ssh_host
    return "${user}@${hostIp}"
}

function Get-VultrSshPort {
    param($Session)
    if ($Session.ssh_port) { return [int]$Session.ssh_port }
    return 22
}

function Get-VultrSshArgs {
    param($Session)
    $port = Get-VultrSshPort $Session
    return @(
        "-i", $SshKey,
        "-p", "$port",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=120",
        "-o", "ConnectTimeout=20"
    )
}

function ConvertTo-VultrJson {
    param([object]$Object)
    if ($PSVersionTable.PSVersion.Major -ge 7) {
        return ($Object | ConvertTo-Json -Depth 8 -Compress)
    }
    Add-Type -AssemblyName System.Web.Extensions
    $ser = New-Object System.Web.Script.Serialization.JavaScriptSerializer
    $ser.MaxJsonLength = 20MB
    return $ser.Serialize($Object)
}

function Invoke-VultrApi {
    param(
        [string]$Method,
        [string]$Path,
        [object]$Body = $null,
        [string]$JsonBody = ""
    )
    $key = Get-VultrApiKey
    $uri = if ($Path.StartsWith("http")) { $Path } else { "$VultrApiBase$Path" }
    $headers = @{
        Authorization = "Bearer $key"
        Accept        = "application/json"
    }
    try {
        if ($JsonBody) {
            $headers["Content-Type"] = "application/json"
            return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers -Body $JsonBody
        }
        if ($null -eq $Body) {
            return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers
        }
        $headers["Content-Type"] = "application/json"
        $json = ConvertTo-VultrJson $Body
        return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers -Body $json
    }
    catch {
        $code = 0
        $errText = $_.Exception.Message
        $resp = $_.Exception.Response
        if ($resp) {
            $code = [int]$resp.StatusCode
            try {
                $stream = $resp.GetResponseStream()
                if ($stream) {
                    $reader = New-Object System.IO.StreamReader($stream)
                    $errText = $reader.ReadToEnd()
                }
            }
            catch { }
        }
        if ($errText -match "Unauthorized IP") {
            throw "Vultr API 401 Unauthorized IP. Allowlist this host in the Vultr dashboard (API key ACL). Agent last seen IP is in the error body. Body: $errText"
        }
        throw "Vultr API $Method $Path failed (HTTP $code): $errText"
    }
}

function Test-VultrApi {
    $acct = Invoke-VultrApi -Method GET -Path "/account"
    return $acct
}

function Resolve-SftArtifactPath {
    param([string]$Relative)
    $full = Join-Path $RepoRoot $Relative
    if (Test-Path $full) { return (Resolve-Path $full).Path }
    throw "Missing artifact: $full"
}

function Test-VultrSftArtifacts {
    $paths = @(
        "fine_tuning\data\kaggle_upload\spurgeon-qa-mix-v1.zip",
        "fine_tuning\scripts\merge_cpt_lora.py",
        "fine_tuning\scripts\train_sft_sota.py",
        "fine_tuning\scripts\eval_sft_sota.py",
        "fine_tuning\scripts\sft_remote_setup.sh",
        "fine_tuning\scripts\sft_remote_train.sh",
        "fine_tuning\scripts\sft_remote_merge.sh",
        "config.py"
    )
    foreach ($p in $paths) {
        Resolve-SftArtifactPath $p | Out-Null
    }
    Write-Host "Vultr SFT artifacts OK"
}

function Get-VultrUserDataB64 {
    $script = @"
#!/bin/bash
export DEBIAN_FRONTEND=noninteractive
mkdir -p /workspace
apt-get update -y
apt-get install -y python3-pip python3-venv python3-dev unzip
if ! command -v nvidia-smi >/dev/null 2>&1; then
  if [ -x /opt/nvidia/install.sh ]; then
    /opt/nvidia/install.sh || true
  elif [ -x /opt/nvidia/linux_gpu.sh ]; then
    bash /opt/nvidia/linux_gpu.sh || true
  fi
fi
"@
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($script)
    return [Convert]::ToBase64String($bytes)
}

function Resolve-VultrGpuOsId {
    $os = Invoke-VultrApi -Method GET -Path "/os?per_page=500"
    $list = @($os.os)
    $gpu24 = $list | Where-Object { $_.name -match "Ubuntu 24\.04" -and $_.name -match "GPU" } | Select-Object -First 1
    if ($gpu24) {
        Write-Host "OS pick (GPU Ubuntu 24.04): $($gpu24.id) $($gpu24.name)"
        return [int]$gpu24.id
    }
    $u24 = $list | Where-Object { $_.name -match "Ubuntu 24\.04" -and $_.arch -eq "x64" } | Select-Object -First 1
    if ($u24) {
        Write-Host "OS pick (Ubuntu 24.04): $($u24.id) $($u24.name) - install NVIDIA driver via cloud-init if needed"
        return [int]$u24.id
    }
    Write-Host "OS fallback $DefaultOsId"
    return $DefaultOsId
}

function Ensure-VultrSshKeyId {
    $pub = Get-SshPublicKey
    $existing = Invoke-VultrApi -Method GET -Path "/ssh-keys"
    foreach ($k in @($existing.ssh_keys)) {
        $remote = ([string]$k.ssh_key).Trim()
        if ($remote -eq $pub) {
            Write-Host "Using existing Vultr SSH key $($k.id) ($($k.name))"
            return [string]$k.id
        }
    }
    Write-Host "Uploading SSH public key as $SshKeyName"
    $created = Invoke-VultrApi -Method POST -Path "/ssh-keys" -Body @{
        name    = $SshKeyName
        ssh_key = $pub
    }
    return [string]$created.ssh_key.id
}

function Get-VultrSshBase {
    param($Session)
    return @{
        Target = Get-VultrSshRemote $Session
        Args   = (Get-VultrSshArgs $Session)
        Port   = Get-VultrSshPort $Session
    }
}
