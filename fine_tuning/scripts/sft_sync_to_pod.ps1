# Copy SFT GATE-0 artifacts to /workspace on the pod.
. "$PSScriptRoot\sft_runpod_common.ps1"

$session = Get-SftSession
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready - run sft_wait_ssh.ps1 first"
}

$port = Get-SftSshPort $session
$sshTarget = Get-SftSshRemote $session
$sshArgs = @("-i", $SshKey, "-p", "$port", "-o", "StrictHostKeyChecking=accept-new")
$scpArgsBase = @("-i", $SshKey, "-P", "$port", "-o", "StrictHostKeyChecking=accept-new")

function Scp-ToPod {
    param([string]$Local, [string]$Remote)
    $scpArgs = $scpArgsBase + @("-r", $Local, "${sshTarget}:$Remote")
    & scp @scpArgs
    if ($LASTEXITCODE -ne 0) { throw "scp failed: $Local -> $Remote" }
}

Write-Host "Syncing to $sshTarget ..."
$zip = Resolve-SftArtifactPath "fine_tuning\data\kaggle_upload\spurgeon-qa-mix-v1.zip"
$merge = Resolve-SftArtifactPath "fine_tuning\scripts\merge_cpt_lora.py"
$train = Resolve-SftArtifactPath "fine_tuning\scripts\train_sft_sota.py"
$eval = Resolve-SftArtifactPath "fine_tuning\scripts\eval_sft_sota.py"
$stopUtils = Resolve-SftArtifactPath "fine_tuning\scripts\sft_stop_token_utils.py"
$stopVerify = Resolve-SftArtifactPath "fine_tuning\scripts\verify_sft_stop_tokens.py"
$setup = Resolve-SftArtifactPath "fine_tuning\scripts\sft_remote_setup.sh"
$remoteTrain = Resolve-SftArtifactPath "fine_tuning\scripts\sft_remote_train.sh"
$remoteMerge = Resolve-SftArtifactPath "fine_tuning\scripts\sft_remote_merge.sh"
$config = Resolve-SftArtifactPath "config.py"

& ssh @($sshArgs + @($sshTarget, "mkdir -p /workspace"))

Scp-ToPod $zip "/workspace/spurgeon-qa-mix-v1.zip"
Scp-ToPod $merge "/workspace/merge_cpt_lora.py"
Scp-ToPod $train "/workspace/train_sft_sota.py"
Scp-ToPod $eval "/workspace/eval_sft_sota.py"
Scp-ToPod $stopUtils "/workspace/sft_stop_token_utils.py"
Scp-ToPod $stopVerify "/workspace/verify_sft_stop_tokens.py"
Scp-ToPod $setup "/workspace/sft_remote_setup.sh"
Scp-ToPod $remoteTrain "/workspace/sft_remote_train.sh"
Scp-ToPod $remoteMerge "/workspace/sft_remote_merge.sh"
Scp-ToPod $config "/workspace/config.py"

& ssh @($sshArgs + @($sshTarget, "chmod +x /workspace/sft_remote_setup.sh /workspace/sft_remote_train.sh /workspace/sft_remote_merge.sh"))
Write-Host "Sync complete."
