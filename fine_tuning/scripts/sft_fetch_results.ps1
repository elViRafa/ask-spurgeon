# Scp SFT GATE-0 results from pod to local fine_tuning/kaggle/runpod_sft_gate0/
param(
    [string]$LocalDir = ""
)

. "$PSScriptRoot\sft_runpod_common.ps1"

$session = Get-SftSession
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready"
}

if (-not $LocalDir) {
    $LocalDir = $LocalResultsDir
}
New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null

$port = Get-SftSshPort $session
$sshTarget = Get-SftSshRemote $session
$scpArgsBase = @("-i", $SshKey, "-P", "$port", "-o", "StrictHostKeyChecking=accept-new")

$remotePaths = @(
    "/workspace/spurgeon_qa_lora_v2",
    "/workspace/sft_train.log",
    "/workspace/sft_run_config.json",
    "/workspace/sft_eval_metrics.json",
    "/workspace/theology_cpt_v2_merged_hf",
    "/workspace/spurgeon_qa_v2_merged_hf"
)

foreach ($remotePath in $remotePaths) {
    $name = Split-Path $remotePath -Leaf
    $dest = Join-Path $LocalDir $name
    Write-Host "Fetching $remotePath ..."
    & scp @($scpArgsBase + @("-r", "${sshTarget}:$remotePath", $dest))
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "scp failed for $remotePath (may not exist yet)"
    }
}

Write-Host "Results under $LocalDir"
