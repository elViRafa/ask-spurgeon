# Pull complete SFT checkpoints from pod to local backup.
param(
    [string]$LocalDir = ""
)

. "$PSScriptRoot\sft_runpod_common.ps1"

$session = Get-SftSession
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready"
}

if (-not $LocalDir) {
    $LocalDir = Join-Path $LocalResultsDir "checkpoints"
}
New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null

$port = Get-SftSshPort $session
$sshTarget = Get-SftSshRemote $session
$sshArgs = @("-i", $SshKey, "-p", "$port", "-o", "StrictHostKeyChecking=accept-new")
$scpArgsBase = @("-i", $SshKey, "-P", "$port", "-o", "StrictHostKeyChecking=accept-new")

$listCmd = "find /workspace/spurgeon_qa_lora_v2/checkpoints -maxdepth 1 -type d -name 'checkpoint-*' 2>/dev/null | sort -V"
$remoteList = & ssh @($sshArgs + @($sshTarget, $listCmd))
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Could not list remote checkpoints (may not exist yet)"
    exit 0
}

$synced = 0
foreach ($ckptPath in ($remoteList -split "`n" | Where-Object { $_.Trim() })) {
    $ckptPath = $ckptPath.Trim()
    $name = Split-Path $ckptPath -Leaf
    $stateRemote = "$ckptPath/trainer_state.json"
    $check = & ssh @($sshArgs + @($sshTarget, "test -f '$stateRemote' && echo OK"))
    if ($check -notmatch "OK") {
        Write-Host "Skip $name (incomplete)"
        continue
    }

    $dest = Join-Path $LocalDir $name
    if (Test-Path (Join-Path $dest "trainer_state.json")) {
        Write-Host "Skip $name (already local)"
        continue
    }

    Write-Host "Fetching $name ..."
    if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
    & scp @($scpArgsBase + @("-r", "${sshTarget}:$ckptPath", $dest))
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "scp failed for $name"
        continue
    }
    $synced++
}

Write-Host "Checkpoint sync done ($synced new) -> $LocalDir"
