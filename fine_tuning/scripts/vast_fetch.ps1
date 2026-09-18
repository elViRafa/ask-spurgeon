# Fetch SFT / GATE-0 artifacts from Vast. Skip missing paths.
param(
    [switch]$PartialOnly,
    [string]$LocalDir = ""
)

. "$PSScriptRoot\vast_common.ps1"

if (-not $LocalDir) {
    $LocalDir = $LocalResultsDir
}

$session = Get-VastSession
if (-not $session -or -not $session.ssh_host) {
    Write-Warning "SSH not ready - skip fetch"
    exit 0
}

New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null

$sshTarget = Get-VastSshRemote $session
$port = Get-VastSshPort $session
$sshArgs = Get-VastSshArgs $session
$scpArgsBase = @(
    "-i", $SshKey,
    "-P", "$port",
    "-o", "StrictHostKeyChecking=accept-new"
)

$remotePaths = @(
    "/kaggle/working/spurgeon_qa_lora_v2",
    "/workspace/spurgeon_qa_lora_v2",
    "/workspace/spurgeon_qa_merged_hf",
    "/workspace/sft_merge_sft.log",
    "/workspace/sft_train.log",
    "/workspace/sft_launch.log",
    "/kaggle/working/sft_run_config.json",
    "/workspace/sft_run_config.json",
    "/kaggle/working/stop_token_s3_audit.json",
    "/workspace/stop_token_s3_audit.json",
    "/workspace/stop_token_phase2.json"
)

if (-not $PartialOnly) {
    $remotePaths += @("/workspace/theology_cpt_v2_merged_hf")
}
else {
    $remoteCheck = 'test -f /workspace/theology_cpt_v2_merged_hf/config.json && test -f /workspace/theology_cpt_v2_merged_hf/tokenizer_config.json && echo COMPLETE || echo INCOMPLETE'
    $check = & ssh @($sshArgs + @($sshTarget, $remoteCheck))
    if ($check -match "COMPLETE") {
        $dest = Join-Path $LocalDir "theology_cpt_v2_merged_hf"
        $localTok = Join-Path $dest "tokenizer_config.json"
        if (-not (Test-Path $localTok)) {
            Write-Host "Fetching GATE-0 merged HF (complete remote) ..."
            $remotePaths += "/workspace/theology_cpt_v2_merged_hf"
        }
        else {
            Write-Host "Skip GATE-0 merged HF (already local with tokenizer)"
        }
    }
    else {
        Write-Host "Skip merged HF fetch (remote incomplete)"
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

Write-Host "Artifact fetch done ($fetched) paths -> $LocalDir"
