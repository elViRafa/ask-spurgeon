# Pull complete HF checkpoints from pod to local backup (only dirs with trainer_state.json).
param(
    [string]$LocalDir = ""
)

. "$PSScriptRoot\s6_runpod_common.ps1"

$session = Get-S6Session
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready"
}

if (-not $LocalDir) {
    $LocalDir = Join-Path $CptRoot "kaggle\runpod_cpt_v3\s6_continue_b\checkpoints_sota"
}
New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null

$port = Get-S6SshPort $session
$sshTarget = Get-S6SshRemote $session
$sshArgs = @("-i", $SshKey, "-p", "$port", "-o", "StrictHostKeyChecking=accept-new")
$scpArgsBase = @("-i", $SshKey, "-P", "$port", "-o", "StrictHostKeyChecking=accept-new")

$listCmd = "find /workspace/checkpoints_sota -maxdepth 1 -type d -name 'checkpoint-*' 2>/dev/null | sort -V"
$remoteList = & ssh @($sshArgs + @($sshTarget, $listCmd))
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Could not list remote checkpoints"
    exit 1
}

$synced = 0
foreach ($ckptPath in ($remoteList -split "`n" | Where-Object { $_.Trim() })) {
    $ckptPath = $ckptPath.Trim()
    $name = Split-Path $ckptPath -Leaf
    $stateRemote = "$ckptPath/trainer_state.json"
    $check = & ssh @($sshArgs + @($sshTarget, "test -f '$stateRemote' && echo OK"))
    if ($check -notmatch "OK") {
        Write-Host "Skip $name (incomplete - no trainer_state.json)"
        continue
    }

    $dest = Join-Path $LocalDir $name
    if (Test-Path (Join-Path $dest "trainer_state.json")) {
        Write-Host "Skip $name (already local)"
        continue
    }

    Write-Host "Fetching $name ..."
    New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null
    if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }

    & scp @($scpArgsBase + @("-r", "${sshTarget}:$ckptPath", $dest))
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "scp failed for $name"
        continue
    }
    if (-not (Test-Path (Join-Path $dest "trainer_state.json"))) {
        Write-Warning "Fetched $name but trainer_state.json missing - deleting partial copy"
        Remove-Item -Recurse -Force $dest -ErrorAction SilentlyContinue
        continue
    }
    $synced++
}

Write-Host "Checkpoint sync done ($synced new complete checkpoint(s)) -> $LocalDir"
