# Fetch SFT / GATE-0 artifacts to local backup (best-effort; skips missing paths).
param(
    [switch]$PartialOnly,
    [string]$LocalDir = ""
)

. "$PSScriptRoot\sft_runpod_common.ps1"

if (-not $LocalDir) {
    $repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
    $LocalDir = Join-Path $repo "fine_tuning\kaggle\runpod_sft_gate0"
}

$session = Get-SftSession
if (-not $session -or -not $session.ssh_host) {
    Write-Warning "SSH not ready — skip fetch"
    exit 0
}

New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null

$port = Get-SftSshPort $session
$sshTarget = Get-SftSshRemote $session
$scpArgsBase = @("-i", $SshKey, "-P", "$port", "-o", "StrictHostKeyChecking=accept-new")

# Long GPU work + audit files worth keeping locally
$remotePaths = @(
    "/workspace/spurgeon_qa_lora_v2",
    "/workspace/sft_train.log",
    "/workspace/sft_run_config.json",
    "/workspace/sft_eval_metrics.json",
    "/workspace/stop_token_s3_audit.json",
    "/workspace/stop_token_phase2.json",
    "/workspace/qa_dataset_train",
    "/workspace/qa_dataset_val"
)

if (-not $PartialOnly) {
    $remotePaths += @(
        "/workspace/theology_cpt_v2_merged_hf",
        "/workspace/spurgeon_qa_v2_merged_hf"
    )
}
else {
    # GATE-0 merged HF is expensive to recreate — fetch when config.json exists
    $gate0Marker = "/workspace/theology_cpt_v2_merged_hf/config.json"
    $check = & ssh @("-i", $SshKey, "-p", "$port", "-o", "StrictHostKeyChecking=accept-new", $sshTarget, "test -f '$gate0Marker' && echo OK")
    if ($check -match "OK") {
        $dest = Join-Path $LocalDir "theology_cpt_v2_merged_hf"
        if (-not (Test-Path (Join-Path $dest "config.json"))) {
            Write-Host "Fetching GATE-0 merged HF (one-time, large) ..."
            $remotePaths += "/workspace/theology_cpt_v2_merged_hf"
        }
        else {
            Write-Host "Skip GATE-0 merged HF (already local)"
        }
    }
}

$fetched = 0
foreach ($remotePath in $remotePaths) {
    $name = Split-Path $remotePath -Leaf
    $dest = Join-Path $LocalDir $name
    Write-Host "Fetching $remotePath ..."
    & scp @($scpArgsBase + @("-r", "${sshTarget}:$remotePath", $dest))
    if ($LASTEXITCODE -eq 0) {
        $fetched++
    }
    else {
        Write-Host "  (not present yet)"
    }
}

# Checkpoints via dedicated incremental sync
& "$PSScriptRoot\sft_sync_checkpoints.ps1" -LocalDir (Join-Path $LocalDir "checkpoints")

Write-Host "Artifact fetch done ($fetched paths) -> $LocalDir"
