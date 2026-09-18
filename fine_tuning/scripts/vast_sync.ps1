# Copy SFT GATE-0 artifacts to /workspace on the Vast container.
. "$PSScriptRoot\vast_common.ps1"

$session = Get-VastSession
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready - run vast_wait_ssh.ps1 first"
}

Test-VastSftArtifacts

$sshTarget = Get-VastSshRemote $session
$sshArgs = Get-VastSshArgs $session
$port = Get-VastSshPort $session
$scpArgsBase = @(
    "-i", $SshKey,
    "-P", "$port",
    "-o", "StrictHostKeyChecking=accept-new"
)

function Copy-ToVast {
    param([string]$Local, [string]$Remote)
    $scpArgs = $scpArgsBase + @("-r", $Local, "${sshTarget}:$Remote")
    & scp @scpArgs
    if ($LASTEXITCODE -ne 0) { throw "scp failed: $Local -> $Remote" }
}

Write-Host "Syncing to $sshTarget port=$port ..."
$zip = Resolve-SftArtifactPath "fine_tuning\data\kaggle_upload\spurgeon-qa-mix-v1.zip"
$merge = Resolve-SftArtifactPath "fine_tuning\scripts\merge_cpt_lora.py"
$mergeSft = Resolve-SftArtifactPath "fine_tuning\scripts\merge_sft_lora.py"
$train = Resolve-SftArtifactPath "fine_tuning\scripts\train_sft_sota.py"
$eval = Resolve-SftArtifactPath "fine_tuning\scripts\eval_sft_sota.py"
$stopUtils = Resolve-SftArtifactPath "fine_tuning\scripts\sft_stop_token_utils.py"
$stopVerify = Resolve-SftArtifactPath "fine_tuning\scripts\verify_sft_stop_tokens.py"
$setup = Resolve-SftArtifactPath "fine_tuning\scripts\sft_remote_setup.sh"
$remoteTrain = Resolve-SftArtifactPath "fine_tuning\scripts\sft_remote_train.sh"
$remoteMerge = Resolve-SftArtifactPath "fine_tuning\scripts\sft_remote_merge.sh"
$remoteMergeSft = Resolve-SftArtifactPath "fine_tuning\scripts\sft_remote_merge_sft.sh"
$config = Resolve-SftArtifactPath "config.py"

& ssh @($sshArgs + @($sshTarget, "mkdir -p /workspace"))
if ($LASTEXITCODE -ne 0) { throw "mkdir /workspace failed" }

Copy-ToVast $zip "/workspace/spurgeon-qa-mix-v1.zip"
Copy-ToVast $merge "/workspace/merge_cpt_lora.py"
Copy-ToVast $mergeSft "/workspace/merge_sft_lora.py"
Copy-ToVast $train "/workspace/train_sft_sota.py"
Copy-ToVast $eval "/workspace/eval_sft_sota.py"
Copy-ToVast $stopUtils "/workspace/sft_stop_token_utils.py"
Copy-ToVast $stopVerify "/workspace/verify_sft_stop_tokens.py"
Copy-ToVast $setup "/workspace/sft_remote_setup.sh"
Copy-ToVast $remoteTrain "/workspace/sft_remote_train.sh"
Copy-ToVast $remoteMerge "/workspace/sft_remote_merge.sh"
Copy-ToVast $remoteMergeSft "/workspace/sft_remote_merge_sft.sh"
Copy-ToVast $config "/workspace/config.py"

& ssh @($sshArgs + @($sshTarget, "chmod +x /workspace/sft_remote_setup.sh /workspace/sft_remote_train.sh /workspace/sft_remote_merge.sh /workspace/sft_remote_merge_sft.sh"))
if ($LASTEXITCODE -ne 0) { throw "chmod failed" }
Write-Host "Sync complete."
