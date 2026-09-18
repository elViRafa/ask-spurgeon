# On-pod C eval — S6 partial (default: best HF checkpoint-2050) or post-complete B.
param(
    [string]$CheckpointName = "checkpoint-2050",
    [switch]$NoFetch
)

. "$PSScriptRoot\s6_runpod_common.ps1"

$session = Get-S6Session
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready"
}

$hostIp = [string]$session.ssh_host
$port = Get-S6SshPort $session
$sshTarget = Get-S6SshRemote $session
$eval = Resolve-ArtifactPath "scripts\eval_cpt_sota.py"
$remote = Resolve-ArtifactPath "scripts\s6_remote_c_eval.sh"

$sshArgs = @("-i", $SshKey, "-p", "$port", "-o", "StrictHostKeyChecking=accept-new")
$scpArgsBase = @("-i", $SshKey, "-P", "$port", "-o", "StrictHostKeyChecking=accept-new")

& scp @($scpArgsBase + @($eval, "${sshTarget}:/workspace/eval_cpt_sota.py"))
& scp @($scpArgsBase + @($remote, "${sshTarget}:/workspace/s6_remote_c_eval.sh"))
& ssh @($sshArgs + @($sshTarget, "chmod +x /workspace/s6_remote_c_eval.sh"))

Write-Host "Launching C eval on $CheckpointName (S6 partial, training incomplete, resume later)"
$remoteCmd = 'export S6_EVAL_CHECKPOINT=/workspace/checkpoints_sota/' + $CheckpointName + '; /workspace/s6_remote_c_eval.sh'
& ssh @($sshArgs + @($sshTarget, $remoteCmd))
if ($LASTEXITCODE -ne 0) { throw "C eval launch failed" }

if (-not $NoFetch) {
    $localEval = Join-Path $CptRoot "kaggle\runpod_cpt_v3\s6_c_eval"
    New-Item -ItemType Directory -Force -Path $localEval | Out-Null
    & scp @($scpArgsBase + @("${sshTarget}:/workspace/cpt_eval.log", $localEval))
    & scp @($scpArgsBase + @("${sshTarget}:/workspace/theology_cpt_eval_metrics.json", $localEval)) 2>$null
    Write-Host "Eval artifacts -> $localEval"
}

# Update session
$sessionObj = Get-S6Session
if ($sessionObj) {
    $ht = @{}
    $sessionObj.PSObject.Properties | ForEach-Object { $ht[$_.Name] = $_.Value }
    $ht["c_eval_checkpoint"] = $CheckpointName
    $ht["c_eval_status"] = "launched"
    $ht["training_complete"] = $false
    $ht["resume_from_checkpoint"] = "checkpoint-2100"
    Save-S6Session $ht
}

Write-Host "C eval running on pod. Tail: tail -f /workspace/cpt_eval.log via SSH"
