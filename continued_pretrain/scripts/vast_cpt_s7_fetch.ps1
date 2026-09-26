# Fetch S7 Phase A artifacts from Vast. Pulls checkpoints_s7 + s5best. Does NOT train.
param(
    [string]$LocalDir = ""
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\vast_cpt_s7_common.ps1"

$session = Get-VastSession
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready"
}

if (-not $LocalDir) {
    $LocalDir = Join-Path $env:VAST_LOCAL_RESULTS_DIR "fetch"
}
New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null
$ckptDir = Join-Path $LocalDir "checkpoints_s7"
New-Item -ItemType Directory -Force -Path $ckptDir | Out-Null

$port = Get-VastSshPort $session
$target = Get-VastSshRemote $session
$sshArgs = (Get-VastSshArgs $session)
$scpBase = @("-i", $SshKey, "-P", "$port", "-o", "StrictHostKeyChecking=accept-new")

function Pull([string]$Remote, [string]$Local) {
    Write-Host "scp $Remote -> $Local"
    & scp @($scpBase + @("-r", "${target}:$Remote", $Local))
    if ($LASTEXITCODE -ne 0) { Write-Warning "scp failed: $Remote" }
}

$listCmd = "find /workspace/checkpoints_s7 -maxdepth 1 -type d -name 'checkpoint-*' 2>/dev/null | sort -V"
$remoteList = & ssh @($sshArgs + @($target, $listCmd))
foreach ($ckptPath in ($remoteList -split "`n" | Where-Object { $_.Trim() })) {
    $ckptPath = $ckptPath.Trim()
    $name = Split-Path $ckptPath -Leaf
    $check = & ssh @($sshArgs + @($target, "test -f '$ckptPath/trainer_state.json' && echo OK"))
    if ($check -notmatch "OK") {
        Write-Host "Skip $name (incomplete)"
        continue
    }
    $dest = Join-Path $ckptDir $name
    if (Test-Path (Join-Path $dest "trainer_state.json")) {
        Write-Host "Skip $name (already local)"
        continue
    }
    if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
    Pull $ckptPath $dest
}

Pull "/workspace/cpt_train.log" (Join-Path $LocalDir "cpt_train.log")
Pull "/workspace/theology_cpt_run_config.json" (Join-Path $LocalDir "theology_cpt_run_config.json")
Pull "/workspace/theology_cpt_lora" (Join-Path $LocalDir "theology_cpt_lora")
# §5 candidate exporter (may be absent early in the run)
$s5best = & ssh @($sshArgs + @($target, "test -d /workspace/theology_cpt_lora_s5best && echo OK"))
if ($s5best -match "OK") {
    Pull "/workspace/theology_cpt_lora_s5best" (Join-Path $LocalDir "theology_cpt_lora_s5best")
}
$s5json = & ssh @($sshArgs + @($target, "test -f /workspace/s5_best.json && echo OK"))
if ($s5json -match "OK") {
    Pull "/workspace/s5_best.json" (Join-Path $LocalDir "s5_best.json")
}
Write-Host "Fetch complete -> $LocalDir"
