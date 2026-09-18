# Shared helpers for Vast.ai GATE-0 SFT. Never print VAST_API_KEY / HF_TOKEN.
$ErrorActionPreference = "Stop"

$Script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Script:FtRoot = Join-Path $RepoRoot "fine_tuning"
$Script:SshKey = Join-Path $env:USERPROFILE ".ssh\runpod_cpt"
$Script:HubV2AdapterSha = "319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478"
$Script:Gate0MergedRemote = "/workspace/theology_cpt_v2_merged_hf"
$Script:StateFile = Join-Path $FtRoot "kaggle\vast_sft_session.json"
$Script:LocalResultsDir = Join-Path $FtRoot "kaggle\vast_sft_gate0"
if ($env:VAST_SESSION_FILE -and $env:VAST_SESSION_FILE.Trim()) {
    $Script:StateFile = $env:VAST_SESSION_FILE.Trim()
}
if ($env:VAST_LOCAL_RESULTS_DIR -and $env:VAST_LOCAL_RESULTS_DIR.Trim()) {
    $Script:LocalResultsDir = $env:VAST_LOCAL_RESULTS_DIR.Trim()
}
$Script:DefaultImage = "nvidia/cuda:12.4.1-devel-ubuntu22.04"
$Script:DefaultDiskGb = 100
$Script:DefaultLabel = "sft-gate0"
# Prefer full GPUs — fractional (gpu_frac<1) NVML-spoofs as 3090 and SIGSEGVs Unsloth at step 1.
# cuda_max_good>=12.6 required for torch 2.11+cu126 (driver 535 / CUDA 12.4 fails with error 804).
$Script:SearchQuery = "num_gpus=1 gpu_name=RTX_4090 reliability>=0.95 disk_space>=100 gpu_frac>=1 cuda_max_good>=12.6"
$Script:MaxWallHours = 10

function Get-VastAiExe {
    $venvVast = Join-Path $RepoRoot ".venv\Scripts\vastai.exe"
    if (Test-Path $venvVast) { return $venvVast }
    $cmd = Get-Command vastai -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    throw "vastai CLI not found. Install into .venv or put vastai on PATH."
}

function Get-VastApiKey {
    if ($env:VAST_API_KEY -and $env:VAST_API_KEY.Trim()) {
        return $env:VAST_API_KEY.Trim()
    }
    $dotenv = Join-Path $RepoRoot ".env"
    if (Test-Path $dotenv) {
        foreach ($line in Get-Content $dotenv) {
            $t = $line.Trim()
            if ($t.StartsWith("VAST_API_KEY=")) {
                $v = $t.Substring("VAST_API_KEY=".Length).Trim().Trim('"').Trim("'")
                if ($v) { return $v }
            }
        }
    }
    $cfg = Join-Path $env:USERPROFILE ".config\vastai\vast_api_key"
    if (Test-Path $cfg) {
        $v = (Get-Content $cfg -Raw).Trim()
        if ($v) { return $v }
    }
    throw "VAST_API_KEY not set. Add it to .env (never commit) or ~/.config/vastai/vast_api_key."
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

function Save-VastSession {
    param([hashtable]$Data)
    $dir = Split-Path $StateFile -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $json = $Data | ConvertTo-Json -Depth 8
    [System.IO.File]::WriteAllText($StateFile, $json, [System.Text.UTF8Encoding]::new($false))
}

function Get-VastSession {
    if (-not (Test-Path $StateFile)) { return $null }
    return Get-Content $StateFile -Raw -Encoding utf8 | ConvertFrom-Json
}

function Convert-SessionToHashtable {
    param($Session)
    $ht = @{}
    if (-not $Session) { return $ht }
    $Session.PSObject.Properties | ForEach-Object { $ht[$_.Name] = $_.Value }
    return $ht
}

function Invoke-Vastai {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$CliArgs,
        [switch]$RawJson
    )
    $exe = Get-VastAiExe
    $key = Get-VastApiKey
    $all = @("--api-key", $key)
    if ($RawJson) { $all += "--raw" }
    $all += $CliArgs
    $out = & $exe @all 2>&1
    $text = ($out | ForEach-Object { "$_" }) -join "`n"
    if ($LASTEXITCODE -ne 0) {
        throw "vastai $($CliArgs -join ' ') failed (exit $LASTEXITCODE): $text"
    }
    return $text
}

function Invoke-VastaiJson {
    param([string[]]$CliArgs)
    $text = Invoke-Vastai -CliArgs $CliArgs -RawJson
    $start = $text.IndexOf("{")
    $startArr = $text.IndexOf("[")
    if ($startArr -ge 0 -and ($start -lt 0 -or $startArr -lt $start)) {
        $start = $startArr
    }
    if ($start -lt 0) {
        throw "vastai returned no JSON: $text"
    }
    $jsonText = $text.Substring($start)
    return $jsonText | ConvertFrom-Json
}

function Get-VastSshRemote {
    param($Session)
    $user = if ($Session.ssh_user) { [string]$Session.ssh_user } else { "root" }
    $hostIp = [string]$Session.ssh_host
    return "${user}@${hostIp}"
}

function Get-VastSshPort {
    param($Session)
    if ($Session.ssh_port) { return [int]$Session.ssh_port }
    return 22
}

function Get-VastSshArgs {
    param($Session)
    $port = Get-VastSshPort $Session
    return @(
        "-i", $SshKey,
        "-p", "$port",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=120",
        "-o", "ConnectTimeout=20"
    )
}

function Resolve-SftArtifactPath {
    param([string]$Relative)
    $full = Join-Path $RepoRoot $Relative
    if (Test-Path $full) { return (Resolve-Path $full).Path }
    throw "Missing artifact: $full"
}

function Test-VastSftArtifacts {
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
    Write-Host "Vast SFT artifacts OK"
}

function Parse-VastSshUrl {
    param([string]$Url)
    if ($Url -match "ssh://([^@]+)@([^:/]+):(\d+)") {
        return @{
            ssh_user = $Matches[1]
            ssh_host = $Matches[2]
            ssh_port = [int]$Matches[3]
        }
    }
    throw "Could not parse ssh-url: $Url"
}

function Update-VastSessionSshFromInstance {
    param([string]$InstanceId)
    $urlText = Invoke-Vastai -CliArgs @("ssh-url", "$InstanceId")
    $urlLine = ($urlText -split "`n" | Where-Object { $_ -match "ssh://" } | Select-Object -First 1)
    if (-not $urlLine) {
        throw "ssh-url returned no ssh:// line for $InstanceId : $urlText"
    }
    $parsed = Parse-VastSshUrl $urlLine.Trim()
    $session = Get-VastSession
    $ht = Convert-SessionToHashtable $session
    $ht.instance_id = "$InstanceId"
    $ht.ssh_user = $parsed.ssh_user
    $ht.ssh_host = $parsed.ssh_host
    $ht.ssh_port = $parsed.ssh_port
    $ht.ssh_url = $urlLine.Trim()
    Save-VastSession $ht
    return Get-VastSession
}

function Find-VastCheapestOffer {
    param(
        [string]$Query = "",
        [int]$Limit = 5
    )
    if (-not $Query) { $Query = $SearchQuery }
    $offers = Invoke-VastaiJson -CliArgs @(
        "search", "offers", $Query,
        "-d",
        "-o", "dph_total",
        "--limit", "$Limit"
    )
    $list = @($offers)
    if ($list.Count -eq 0) {
        throw "No Vast offers matched: $Query"
    }
    return $list
}
