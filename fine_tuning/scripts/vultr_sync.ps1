# Copy SFT GATE-0 artifacts to /workspace on the Vultr VM.
. "$PSScriptRoot\vultr_common.ps1"

$session = Get-VultrSession
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready - run vultr_wait_ssh.ps1 first"
}

Test-VultrSftArtifacts

$sshTarget = Get-VultrSshRemote $session
$sshArgs = Get-VultrSshArgs $session
$port = Get-VultrSshPort $session
$scpArgsBase = @(
    "-i", $SshKey,
    "-P", "$port",
    "-o", "StrictHostKeyChecking=accept-new"
)

function Copy-ToVultr {
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
if ($LASTEXITCODE -ne 0) { throw "mkdir /workspace failed" }

Copy-ToVultr $zip "/workspace/spurgeon-qa-mix-v1.zip"
Copy-ToVultr $merge "/workspace/merge_cpt_lora.py"
Copy-ToVultr $train "/workspace/train_sft_sota.py"
Copy-ToVultr $eval "/workspace/eval_sft_sota.py"
Copy-ToVultr $stopUtils "/workspace/sft_stop_token_utils.py"
Copy-ToVultr $stopVerify "/workspace/verify_sft_stop_tokens.py"
Copy-ToVultr $setup "/workspace/sft_remote_setup.sh"
Copy-ToVultr $remoteTrain "/workspace/sft_remote_train.sh"
Copy-ToVultr $remoteMerge "/workspace/sft_remote_merge.sh"
Copy-ToVultr $config "/workspace/config.py"

& ssh @($sshArgs + @($sshTarget, "chmod +x /workspace/sft_remote_setup.sh /workspace/sft_remote_train.sh /workspace/sft_remote_merge.sh"))
if ($LASTEXITCODE -ne 0) { throw "chmod failed" }
Write-Host "Sync complete."
