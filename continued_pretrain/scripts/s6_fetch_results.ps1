# Scp S6 B results from pod to local kaggle/runpod_cpt_v3/s6_continue_b/
param(
    [string]$LocalDir = ""
)

. "$PSScriptRoot\s6_runpod_common.ps1"

$session = Get-S6Session
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready"
}

if (-not $LocalDir) {
    $LocalDir = Join-Path $CptRoot "kaggle\runpod_cpt_v3\s6_continue_b"
}
New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null

$port = Get-S6SshPort $session
$sshTarget = Get-S6SshRemote $session
$scpArgsBase = @("-i", $SshKey, "-P", "$port", "-o", "StrictHostKeyChecking=accept-new")

$remotePaths = @(
    "/workspace/theology_cpt_lora",
    "/workspace/checkpoints_sota",
    "/workspace/cpt_train.log",
    "/workspace/theology_cpt_run_config.json"
)

foreach ($remotePath in $remotePaths) {
    $name = Split-Path $remotePath -Leaf
    $dest = Join-Path $LocalDir $name
    Write-Host "Fetching $remotePath ..."
    & scp @($scpArgsBase + @("-r", "${sshTarget}:$remotePath", $dest))
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "scp failed for $remote (may not exist yet)"
    }
}

Write-Host "Results under $LocalDir"
