# Attach monitor to an already-launched weighted SFT pod (session JSON required).
# Does not provision. On terminal state: fetch adapter/logs then destroy (unless -KeepPod).
param(
    [switch]$KeepPod,
    [double]$MaxWallHours = 10,
    [int]$PollSeconds = 60
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ResultsDir = Join-Path $RepoRoot "fine_tuning\kaggle\runpod_sft_s8_weighted"
$env:SFT_SESSION_FILE = Join-Path $RepoRoot "fine_tuning\kaggle\runpod_sft_s8_weighted_session.json"
$env:SFT_LOCAL_RESULTS_DIR = $ResultsDir
. "$PSScriptRoot\sft_runpod_common.ps1"

$SshKey = Join-Path $env:USERPROFILE ".ssh\runpod_cpt"
New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null

function Get-AttachState {
    $sess = Get-SftSession
    if (-not $sess -or -not $sess.ssh_host) { throw "session missing ssh" }
    $port = Get-SftSshPort $sess
    $target = Get-SftSshRemote $sess
    $out = & ssh -i $SshKey -o StrictHostKeyChecking=no -o ConnectTimeout=20 -p "$port" $target "bash /workspace/sft_weighted_state_probe.sh"
    $text = ($out | Out-String)
    $state = "UNKNOWN"
    if ($text -match "WEIGHTED_STATE=([A-Z0-9_]+)") { $state = $Matches[1] }
    return [pscustomobject]@{ State = $state; Raw = $text }
}

function Save-AttachFetch {
    $sess = Get-SftSession
    if (-not $sess -or -not $sess.ssh_host) { return }
    $port = Get-SftSshPort $sess
    $target = Get-SftSshRemote $sess
    $scpBase = @("-i", $SshKey, "-P", "$port", "-o", "StrictHostKeyChecking=accept-new", "-o", "LogLevel=ERROR")
    foreach ($rp in @(
            "/workspace/sft_s8_weighted",
            "/workspace/sft_setup.log",
            "/workspace/sft_launch.log",
            "/workspace/sft_smoke.log",
            "/workspace/sft_train.log",
            "/workspace/sft_pip_freeze.txt"
        )) {
        $prev = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try { & scp @($scpBase + @("-r", "${target}:${rp}", $ResultsDir)) 2>$null } catch { }
        finally { $ErrorActionPreference = $prev }
    }
    Write-Host "FETCH_DIR=$ResultsDir"
}

function Invoke-AttachDestroy([string]$Reason) {
    if ($KeepPod) {
        Write-Warning "KeepPod set; not destroying ($Reason)"
        return
    }
    $sess = Get-SftSession
    if (-not $sess -or -not $sess.pod_id) {
        Write-Warning "No pod_id to destroy ($Reason)"
        return
    }
    $podId = [string]$sess.pod_id
    Write-Host "Destroying RunPod pod $podId reason=$Reason"
    try {
        Invoke-RunpodRestV1 -Method DELETE -Path "/pods/$podId" | Out-Null
        Write-Host "POD_DELETED=$podId"
    }
    catch {
        Write-Warning ("DELETE pod failed: {0}" -f $_.Exception.Message)
        if (Test-Path $Runpodctl) { & $Runpodctl pod delete $podId 2>&1 | Out-Null }
    }
}

$sess = Get-SftSession
if (-not $sess -or -not $sess.pod_id) { throw "No live session" }
Write-Host ("ATTACH_MONITOR pod={0} max_wall_h={1} keep_pod={2} usd_per_hr~0.89 Secure 4090" -f $sess.pod_id, $MaxWallHours, $KeepPod)
$deadline = [datetime]::UtcNow.AddHours($MaxWallHours)
$deadStreak = 0
$aliveSeen = $false

while ([datetime]::UtcNow -lt $deadline) {
    $st = Get-AttachState
    $ts = [datetime]::UtcNow.ToString("u")
    Write-Host "[$ts] WEIGHTED_STATE=$($st.State)"
    if ($st.Raw -match "SETUP_SIZE=(\d+)") { Write-Host "  setup_size=$($Matches[1])" }
    if ($st.Raw -match "TRAIN_SIZE=(\d+)") { Write-Host "  train_size=$($Matches[1])" }

    if ($st.State -eq "SMOKE_BEFORE_TRAIN_FAILED" -or $st.State -eq "SETUP_FAILED") {
        Write-Warning "Fail state $($st.State)"
        Save-AttachFetch
        Invoke-AttachDestroy $st.State
        exit 1
    }
    if ($st.State -eq "SMOKE_ONLY_DONE") {
        Write-Host "SMOKE_ONLY_DONE"
        Save-AttachFetch
        Invoke-AttachDestroy "SMOKE_ONLY_DONE"
        exit 0
    }
    if ($st.State -eq "ALIVE") {
        $aliveSeen = $true
        $deadStreak = 0
    }
    elseif ($st.State -eq "DEAD" -and $aliveSeen) {
        $deadStreak++
        Write-Host "DEAD streak $deadStreak/3"
        if ($deadStreak -ge 3) {
            Save-AttachFetch
            Invoke-AttachDestroy "train_dead"
            exit 0
        }
    }
    Start-Sleep -Seconds $PollSeconds
}

Write-Warning "Wall clock hit"
Save-AttachFetch
Invoke-AttachDestroy "max_wall"
exit 0
