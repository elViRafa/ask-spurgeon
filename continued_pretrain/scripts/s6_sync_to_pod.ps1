# Copy S6 continue-B artifacts to /workspace on the pod.
. "$PSScriptRoot\s6_runpod_common.ps1"

$session = Get-S6Session
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready - run s6_wait_ssh.ps1 first"
}

$port = Get-S6SshPort $session
$sshTarget = Get-S6SshRemote $session
$sshArgs = @("-i", $SshKey, "-p", "$port", "-o", "StrictHostKeyChecking=accept-new")
$scpArgsBase = @("-i", $SshKey, "-P", "$port", "-o", "StrictHostKeyChecking=accept-new")

function Scp-ToPod {
    param([string]$Local, [string]$Remote)
    $scpArgs = $scpArgsBase + @("-r", $Local, "${sshTarget}:$Remote")
    & scp @scpArgs
    if ($LASTEXITCODE -ne 0) { throw "scp failed: $Local -> $Remote" }
}

Write-Host "Syncing to $sshTarget ..."
$dataset = Resolve-ArtifactPath "kaggle\a_output_v3\theology_dataset"
$holdouts = Resolve-ArtifactPath "kaggle\a_output_v3\theology_holdouts"
$manifest = Resolve-ArtifactPath "data\theology_mix_manifest.json"
$lora = Resolve-ArtifactPath "kaggle\runpod_cpt_v3\theology_cpt_lora"
$train = Resolve-ArtifactPath "scripts\train_cpt_sota.py"
$runtime = Resolve-ArtifactPath "scripts\cpt_runtime.py"
$remoteTrain = Resolve-ArtifactPath "scripts\s6_remote_continue_b.sh"

& ssh @($sshArgs + @($sshTarget, "mkdir -p /workspace"))

Scp-ToPod $dataset "/workspace/"
Scp-ToPod $holdouts "/workspace/"
Scp-ToPod $manifest "/workspace/theology_mix_manifest.json"
Scp-ToPod $lora "/workspace/"
Scp-ToPod $train "/workspace/train_cpt_sota.py"
Scp-ToPod $runtime "/workspace/cpt_runtime.py"
Scp-ToPod $remoteTrain "/workspace/s6_remote_continue_b.sh"

& ssh @($sshArgs + @($sshTarget, "chmod +x /workspace/s6_remote_continue_b.sh"))
Write-Host "Sync complete."
