# RunPod Unsloth weighted SFT on S8 merged CPT: RAG mix + open-theology slice.
# Default: local readiness only. Does not rent and does not contact RunPod.
# Forge runs -Go after operator go: provision, sync, train (or -SmokeOnly), fetch, destroy.
# Do NOT call vast_sft_s8_weighted_orchestrate.ps1 or GATE-0 sft_orchestrate.ps1 for this path.
# Sync: pinned sparse-checkout on GPU; SCP only dirty overrides (-AllowDirtySync).
param(
    [switch]$Go,
    [switch]$SmokeOnly,
    [switch]$AllowDirtySync,
    [switch]$StartMonitor,
    [switch]$KeepPod,
    [ValidateSet("COMMUNITY", "SECURE")]
    [string]$CloudType = "COMMUNITY",
    [int]$TimeoutMinutes = 45,
    [int]$LoadingTimeoutMinutes = 45,
    [double]$MaxWallHours = 10,
    [double]$QuoteUsdPerHour = 0.34
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$FtRoot = Join-Path $RepoRoot "fine_tuning"
$SessionFile = Join-Path $FtRoot "kaggle\runpod_sft_s8_weighted_session.json"
$ResultsDir = Join-Path $FtRoot "kaggle\runpod_sft_s8_weighted"
$PlanPy = Join-Path $PSScriptRoot "sft_s8_weighted_runpod_unsloth_plan.py"
$Label = "sft-s8-weighted-unsloth"
$GitHubRepoUrl = "https://github.com/elViRafa/ask-spurgeon.git"
$SparseConePaths = @("fine_tuning/data", "fine_tuning/scripts")
$SshKey = Join-Path $env:USERPROFILE ".ssh\runpod_cpt"

# -Go without a local monitor left GATE-0 / Vast runs billing after setup fail.
if ($Go -and -not $StartMonitor) {
    Write-Warning "WARNING: -Go without -StartMonitor - forcing StartMonitor (dead-launcher billing risk)."
    Write-Host "GO_IMPLIES_START_MONITOR=1"
    $StartMonitor = $true
}

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
$TranscriptPath = Join-Path $ResultsDir ("orchestrate_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log")
try {
    Start-Transcript -Path $TranscriptPath -Append | Out-Null
    Write-Host "TRANSCRIPT=$TranscriptPath"
}
catch {
    Write-Warning ("Start-Transcript failed (continuing): {0}" -f $_.Exception.Message)
}

$WeightedSyncMap = @(
    @{ Rel = "fine_tuning/scripts/train_sft_sota.py"; Remote = "/workspace/train_sft_sota.py" }
    @{ Rel = "fine_tuning/scripts/sft_stop_token_utils.py"; Remote = "/workspace/sft_stop_token_utils.py" }
    @{ Rel = "fine_tuning/scripts/sft_remote_setup.sh"; Remote = "/workspace/sft_remote_setup.sh" }
    @{ Rel = "fine_tuning/scripts/sft_remote_train_s8_weighted.sh"; Remote = "/workspace/sft_remote_train_s8_weighted.sh" }
    @{ Rel = "fine_tuning/scripts/sft_setup_fail_watchdog.sh"; Remote = "/workspace/sft_setup_fail_watchdog.sh" }
    @{ Rel = "fine_tuning/scripts/sft_setup_markers.sh"; Remote = "/workspace/sft_setup_markers.sh" }
    @{ Rel = "fine_tuning/scripts/sft_weighted_state_probe.sh"; Remote = "/workspace/sft_weighted_state_probe.sh" }
    @{ Rel = "fine_tuning/scripts/sft_tokenizer_cpu_smoke.py"; Remote = "/workspace/sft_tokenizer_cpu_smoke.py" }
    @{ Rel = "fine_tuning/scripts/sft_gate0_sep6_constraints.txt"; Remote = "/workspace/sft_gate0_sep6_constraints.txt" }
    @{ Rel = "config.py"; Remote = "/workspace/config.py" }
    @{ Rel = "fine_tuning/data/qa_mix_train.jsonl"; Remote = "/workspace/spurgeon-qa-mix-v1/qa_mix_train.jsonl" }
    @{ Rel = "fine_tuning/data/qa_mix_val.jsonl"; Remote = "/workspace/spurgeon-qa-mix-v1/qa_mix_val.jsonl" }
    @{ Rel = "fine_tuning/data/qa_open_theology/sft/open_theology_train.jsonl"; Remote = "/workspace/qa_open_theology/sft/open_theology_train.jsonl" }
    @{ Rel = "fine_tuning/data/qa_open_theology/sft/open_theology_eval.jsonl"; Remote = "/workspace/qa_open_theology/sft/open_theology_eval.jsonl" }
    @{ Rel = "fine_tuning/data/qa_open_theology/sft/manifest.json"; Remote = "/workspace/qa_open_theology/sft/manifest.json" }
)

function Get-PinnedSha {
    $sha = (& git -C $RepoRoot rev-parse HEAD 2>$null | Out-String).Trim()
    if (-not $sha -or $sha.Length -lt 7) { throw "git rev-parse HEAD failed in $RepoRoot" }
    return $sha
}

function Get-DirtyWeightedSyncOverrides {
    $dirty = @()
    foreach ($entry in $WeightedSyncMap) {
        $rel = $entry.Rel
        $status = (& git -C $RepoRoot status --porcelain -- $rel 2>$null | Out-String).Trim()
        if ($status) {
            $dirty += [pscustomobject]@{
                Rel    = $rel
                Local  = Join-Path $RepoRoot ($rel -replace "/", "\")
                Remote = $entry.Remote
                Status = $status
            }
        }
    }
    return $dirty
}

function Write-WeightedSyncBanner {
    param(
        [string]$PinnedSha,
        [object[]]$DirtyOverrides
    )
    Write-Host "PINNED_SHA=$PinnedSha"
    Write-Host ("SPARSE_CONE={0}" -f ($SparseConePaths -join " "))
    Write-Host "REPO_URL=$GitHubRepoUrl"
    Write-Host "HOST=runpod BACKEND=unsloth"
    Write-Host "SYNC_PATHS (materialize after sparse-checkout):"
    foreach ($entry in $WeightedSyncMap) {
        Write-Host ("  {0} -> {1}" -f $entry.Rel, $entry.Remote)
    }
    if ($DirtyOverrides.Count -eq 0) {
        Write-Host "DIRTY_OVERRIDES=(none) -- GPU pulls tracked files at PINNED_SHA; no jsonl SCP"
    }
    else {
        Write-Host "DIRTY_OVERRIDES:"
        foreach ($d in $DirtyOverrides) {
            Write-Host ("  {0}  ({1})" -f $d.Rel, $d.Status)
        }
        if (-not $AllowDirtySync) {
            Write-Host "DIRTY_SYNC_BLOCKED: pass -AllowDirtySync to SCP dirty overrides after sparse sync (required for -Go)."
        }
        else {
            Write-Host "DIRTY_SYNC_OK: -AllowDirtySync set; dirty paths will SCP after sparse sync."
        }
    }
}

$py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

Write-Host "=== RunPod SFT S8 weighted Unsloth (RAG + open-theology) ==="
Write-Host "go=$Go smoke_only=$SmokeOnly start_monitor=$StartMonitor allow_dirty_sync=$AllowDirtySync (train only if -Go)"
Write-Host "session=$SessionFile"
Write-Host "results=$ResultsDir"
$smokeQuote = [math]::Round($QuoteUsdPerHour * 0.5, 2)
$fullQuote = [math]::Round($QuoteUsdPerHour * $MaxWallHours, 2)
Write-Host ("cost_quote smoke~{0:N2} (0.5h@{1:N2}/hr) full~{2:N2} ({3}h@{1:N2}/hr; adjust QuoteUsdPerHour)" -f $smokeQuote, $QuoteUsdPerHour, $fullQuote, $MaxWallHours)

& $py $PlanPy
if ($LASTEXITCODE -ne 0) { throw "local readiness FAIL" }

$PinnedSha = Get-PinnedSha
$DirtyOverrides = @(Get-DirtyWeightedSyncOverrides)
Write-Host ""
Write-WeightedSyncBanner -PinnedSha $PinnedSha -DirtyOverrides $DirtyOverrides

if (-not $Go) {
    Write-Host ""
    Write-Host "DRY COMPLETE -- no pod rented, no download, no training started."
    Write-Host "No runpodctl, scp, or ssh calls were made."
    Write-Host "Do NOT call vast_sft_s8_weighted_orchestrate.ps1 or sft_orchestrate.ps1 for this path."
    Write-Host "Sync on -Go: sparse-checkout at PINNED_SHA on GPU; SCP only dirty overrides (with -AllowDirtySync)."
    Write-Host "Base: rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit"
    Write-Host "Hub LoRA v2 06354dfc stays. SFT_EXPORT=0 until F gates."
    Write-Host "SFT_BACKEND=unsloth  Output: /workspace/sft_s8_weighted/adapter"
    Write-Host "Forge rents only after Rafael says go:"
    Write-Host "  cd fine_tuning\scripts"
    Write-Host "  .\runpod_sft_s8_weighted_orchestrate.ps1 -Go -SmokeOnly -StartMonitor"
    Write-Host "  .\runpod_sft_s8_weighted_orchestrate.ps1 -Go -StartMonitor"
    if ($DirtyOverrides.Count -gt 0 -and -not $AllowDirtySync) {
        Write-Host "READY with dirty sync paths -- push/commit or use -AllowDirtySync before -Go."
    }
    else {
        Write-Host "READY"
    }
    try { Stop-Transcript | Out-Null } catch { }
    exit 0
}

if ($DirtyOverrides.Count -gt 0 -and -not $AllowDirtySync) {
    throw ("Sync paths dirty vs HEAD ($($DirtyOverrides.Count)). Commit/push, or pass -AllowDirtySync to SCP overrides after sparse-checkout. Dirty: " + (($DirtyOverrides | ForEach-Object { $_.Rel }) -join ", "))
}

# --- -Go only: runpod / ssh / scp below this line ---
$env:SFT_SESSION_FILE = $SessionFile
$env:SFT_LOCAL_RESULTS_DIR = $ResultsDir

. "$PSScriptRoot\sft_runpod_common.ps1"
# Re-assert after common defaults (env already applied inside common).
$Script:StateFile = $SessionFile
$Script:LocalResultsDir = $ResultsDir

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $SessionFile -Parent) | Out-Null

function Get-RunpodSshArgs {
    param($Session)
    $port = Get-SftSshPort $Session
    # -T: RunPod proxy rejects clients that request a PTY without supporting one.
    return @(
        "-T",
        "-i", $SshKey,
        "-p", "$port",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "LogLevel=ERROR",
        "-o", "ConnectTimeout=20",
        "-o", "RequestTTY=no"
    )
}

function Invoke-WeightedSsh([string]$Remote) {
    $session = Get-SftSession
    if (-not $session -or -not $session.ssh_host) {
        throw "SSH not ready"
    }
    $clean = $Remote -replace "`r", ""
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $sshArgs = (Get-RunpodSshArgs $session) + @((Get-SftSshRemote $session), $clean)
        & ssh @sshArgs
        $sx = [int]$LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $prev
    }
    if ($sx -ne 0) {
        throw "ssh failed exit=$sx"
    }
}

function Copy-ToRunpodWeighted {
    param(
        [string]$Local,
        [string]$Remote
    )
    $session = Get-SftSession
    $port = Get-SftSshPort $session
    $remoteHost = Get-SftSshRemote $session
    $remoteDir = (Split-Path $Remote -Parent) -replace "\\", "/"
    if ($remoteDir -and $remoteDir -ne "/" -and $remoteDir -ne ".") {
        Invoke-WeightedSsh "mkdir -p '$remoteDir'"
    }
    $scpArgs = @(
        "-i", $SshKey,
        "-P", "$port",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "LogLevel=ERROR",
        $Local,
        "${remoteHost}:${Remote}"
    )
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & scp @scpArgs
        $sx = [int]$LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $prev
    }
    if ($sx -ne 0) {
        throw "scp failed exit=$sx : $Local -> $Remote"
    }
}

function Sync-WeightedFromGit {
    param(
        [string]$PinnedSha,
        [object[]]$DirtyOverrides
    )
    if ($PinnedSha -notmatch '^[0-9a-fA-F]{7,40}$') {
        throw "invalid PINNED_SHA: $PinnedSha"
    }
    $cone = ($SparseConePaths -join " ")
    $remoteScript = @"
set -euo pipefail
command -v git >/dev/null 2>&1 || { apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git; }
SRC=/workspace/ask-spurgeon-src
SHA='$PinnedSha'
URL='$GitHubRepoUrl'
rm -rf "`$SRC"
mkdir -p "`$SRC" /workspace/spurgeon-qa-mix-v1 /workspace/qa_open_theology/sft /workspace/sft_s8_weighted
git init "`$SRC"
git -C "`$SRC" remote add origin "`$URL"
git -C "`$SRC" sparse-checkout init --cone
git -C "`$SRC" sparse-checkout set $cone
echo "sparse fetch depth=1 SHA=`$SHA ..."
git -C "`$SRC" fetch --depth 1 origin "`$SHA"
git -C "`$SRC" checkout --force FETCH_HEAD
test -f "`$SRC/fine_tuning/data/qa_mix_train.jsonl"
test -f "`$SRC/fine_tuning/scripts/sft_remote_train_s8_weighted.sh"
cp "`$SRC/fine_tuning/data/qa_mix_train.jsonl" /workspace/spurgeon-qa-mix-v1/qa_mix_train.jsonl
cp "`$SRC/fine_tuning/data/qa_mix_val.jsonl" /workspace/spurgeon-qa-mix-v1/qa_mix_val.jsonl
cp "`$SRC/fine_tuning/data/qa_open_theology/sft/open_theology_train.jsonl" /workspace/qa_open_theology/sft/open_theology_train.jsonl
cp "`$SRC/fine_tuning/data/qa_open_theology/sft/open_theology_eval.jsonl" /workspace/qa_open_theology/sft/open_theology_eval.jsonl
cp "`$SRC/fine_tuning/data/qa_open_theology/sft/manifest.json" /workspace/qa_open_theology/sft/manifest.json
cp "`$SRC/fine_tuning/scripts/train_sft_sota.py" /workspace/train_sft_sota.py
cp "`$SRC/fine_tuning/scripts/sft_stop_token_utils.py" /workspace/sft_stop_token_utils.py
cp "`$SRC/fine_tuning/scripts/sft_remote_setup.sh" /workspace/sft_remote_setup.sh
cp "`$SRC/fine_tuning/scripts/sft_remote_train_s8_weighted.sh" /workspace/sft_remote_train_s8_weighted.sh
cp "`$SRC/fine_tuning/scripts/sft_setup_fail_watchdog.sh" /workspace/sft_setup_fail_watchdog.sh
cp "`$SRC/fine_tuning/scripts/sft_setup_markers.sh" /workspace/sft_setup_markers.sh
# Probe may be dirty-only (not yet on PINNED_SHA); dirty SCP fills it next.
cp "`$SRC/fine_tuning/scripts/sft_weighted_state_probe.sh" /workspace/sft_weighted_state_probe.sh 2>/dev/null || true
cp "`$SRC/fine_tuning/scripts/sft_tokenizer_cpu_smoke.py" /workspace/sft_tokenizer_cpu_smoke.py
cp "`$SRC/fine_tuning/scripts/sft_gate0_sep6_constraints.txt" /workspace/sft_gate0_sep6_constraints.txt
git -C "`$SRC" show HEAD:config.py > /workspace/config.py
chmod +x /workspace/sft_remote_setup.sh /workspace/sft_remote_train_s8_weighted.sh /workspace/sft_setup_fail_watchdog.sh /workspace/sft_setup_markers.sh
test -s /workspace/spurgeon-qa-mix-v1/qa_mix_train.jsonl
test -s /workspace/train_sft_sota.py
echo "SPARSE_SYNC_OK sha=`$SHA"
"@
    Write-Host "Syncing weighted SFT via pinned sparse-checkout (no bulk jsonl SCP) ..."
    Write-Host "PINNED_SHA=$PinnedSha"
    Invoke-WeightedSsh $remoteScript
    if ($DirtyOverrides.Count -gt 0) {
        Write-Host ("SCP dirty overrides ({0}) ..." -f $DirtyOverrides.Count)
        foreach ($d in $DirtyOverrides) {
            if (-not (Test-Path -LiteralPath $d.Local)) {
                throw "dirty override missing locally: $($d.Local)"
            }
            Copy-ToRunpodWeighted -Local $d.Local -Remote $d.Remote
        }
    }
    Invoke-WeightedSsh @"
set -euo pipefail
chmod +x /workspace/sft_remote_setup.sh /workspace/sft_remote_train_s8_weighted.sh /workspace/sft_setup_fail_watchdog.sh /workspace/sft_setup_markers.sh
if [ -f /workspace/sft_weighted_state_probe.sh ]; then chmod +x /workspace/sft_weighted_state_probe.sh; fi
test -f /workspace/spurgeon-qa-mix-v1/qa_mix_train.jsonl
test -f /workspace/qa_open_theology/sft/open_theology_train.jsonl
test -f /workspace/sft_remote_setup.sh
test -f /workspace/sft_weighted_state_probe.sh
"@
    Write-Host "Sync complete (sparse + overrides)."
}

function Save-WeightedEvidence {
    param([string]$Reason = "")
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $evDir = Join-Path $ResultsDir ("evidence_" + $stamp)
    New-Item -ItemType Directory -Force -Path $evDir | Out-Null
    $meta = Join-Path $evDir "meta.txt"
    @(
        "reason=$Reason"
        "utc=$((Get-Date).ToUniversalTime().ToString('o'))"
        "session=$SessionFile"
        "backend=unsloth"
        "smoke_only=$SmokeOnly"
    ) | Set-Content -Path $meta -Encoding utf8
    $session = Get-SftSession
    if (-not $session -or -not $session.ssh_host) {
        "ssh_not_ready" | Add-Content $meta
        return
    }
    $port = Get-SftSshPort $session
    $sshTarget = Get-SftSshRemote $session
    $scpBase = @("-i", $SshKey, "-P", "$port", "-o", "StrictHostKeyChecking=accept-new", "-o", "LogLevel=ERROR")
    foreach ($remote in @(
            "/workspace/sft_setup.log",
            "/workspace/sft_launch.log",
            "/workspace/sft_smoke.log",
            "/workspace/sft_train.log",
            "/workspace/sft_pip_freeze.txt"
        )) {
        $name = Split-Path $remote -Leaf
        $prev = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            & scp @($scpBase + @("${sshTarget}:${remote}", (Join-Path $evDir $name))) 2>$null
        }
        catch { }
        finally { $ErrorActionPreference = $prev }
    }
    Write-Host "EVIDENCE=$evDir"
}

function Invoke-DestroyRunpodPod {
    param([string]$Reason)
    if ($KeepPod) {
        Write-Warning "KeepPod set; not destroying ($Reason)"
        return
    }
    $session = Get-SftSession
    if (-not $session -or -not $session.pod_id) {
        Write-Warning "No pod_id to destroy ($Reason)"
        return
    }
    $podId = [string]$session.pod_id
    Write-Host "Destroying RunPod pod $podId reason=$Reason"
    try {
        Invoke-RunpodRestV1 -Method DELETE -Path "/pods/$podId" | Out-Null
        Write-Host "POD_DELETED=$podId"
    }
    catch {
        Write-Warning ("DELETE pod failed: {0}" -f $_.Exception.Message)
        if (Test-Path $Runpodctl) {
            & $Runpodctl pod delete $podId 2>&1 | Out-Null
        }
    }
}

function Invoke-DestroyOnFail {
    param([string]$Reason)
    Write-Host "FAIL: $Reason - evidence then destroy pod to stop billing"
    try { Save-WeightedEvidence -Reason $Reason } catch { Write-Warning $_.Exception.Message }
    Invoke-DestroyRunpodPod -Reason $Reason
    throw $Reason
}

function Get-WeightedTrainState {
    $result = [pscustomobject]@{
        State       = "UNKNOWN"
        PidfileSeen = $false
        SetupMtime  = $null
        SetupSize   = $null
        TrainMtime  = $null
        TrainSize   = $null
        FailMarker  = $null
        TriggerLine = $null
        Raw         = ""
    }
    $session = Get-SftSession
    if (-not $session -or -not $session.ssh_host) {
        return $result
    }
    # Compact probe script (synced to GPU) — avoids Windows ssh argv truncation
    # that previously left the monitor stuck on UNKNOWN through SETUP_FAILED.
    $remote = "bash /workspace/sft_weighted_state_probe.sh"
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $sshArgs = (Get-RunpodSshArgs $session) + @((Get-SftSshRemote $session), $remote)
        $out = & ssh @sshArgs 2>&1 | Out-String
        $sx = [int]$LASTEXITCODE
    }
    catch {
        $result.Raw = $_.Exception.Message
        return $result
    }
    finally {
        $ErrorActionPreference = $prev
    }
    $result.Raw = $out
    if ($sx -ne 0 -and $out -notmatch "WEIGHTED_STATE=") {
        return $result
    }
    if ($out -match "PIDFILE=1") { $result.PidfileSeen = $true }
    if ($out -match "SETUP_MTIME=(\d+)") { $result.SetupMtime = $Matches[1] }
    if ($out -match "SETUP_SIZE=(\d+)") { $result.SetupSize = $Matches[1] }
    if ($out -match "TRAIN_MTIME=(\d+)") { $result.TrainMtime = $Matches[1] }
    if ($out -match "TRAIN_SIZE=(\d+)") { $result.TrainSize = $Matches[1] }
    if ($out -match "FAIL_MARKER=(\S+)") { $result.FailMarker = $Matches[1] }
    if ($out -match "TRIGGER_LINE=(.+)") { $result.TriggerLine = $Matches[1].Trim() }
    if ($out -match "WEIGHTED_STATE=SETUP_FAILED") {
        $result.State = "SETUP_FAILED"
    }
    elseif ($out -match "WEIGHTED_STATE=SMOKE_BEFORE_TRAIN_FAILED") {
        $result.State = "SMOKE_BEFORE_TRAIN_FAILED"
    }
    elseif ($out -match "WEIGHTED_STATE=SMOKE_ONLY_DONE") {
        $result.State = "SMOKE_ONLY_DONE"
    }
    elseif ($out -match "WEIGHTED_STATE=ALIVE") {
        $result.State = "ALIVE"
        $result.PidfileSeen = $true
    }
    elseif ($out -match "WEIGHTED_STATE=DEAD") {
        $result.State = "DEAD"
    }
    else {
        $result.State = "UNKNOWN"
    }
    return $result
}

Write-Host ""
Write-Host "GO: provisioning RunPod GPU for weighted Unsloth SFT"
try {
    & "$PSScriptRoot\sft_provision_pod.ps1" -CloudType $CloudType -PodName $Label -SkipGate0Artifacts
    if ($LASTEXITCODE -ne 0) { throw "provision failed" }

    # Patch session with weighted contract fields (provision may write GATE-0 keys).
    $sess = Get-SftSession
    if (-not $sess) { throw "session missing after provision" }
    $sessHash = @{}
    $sess.PSObject.Properties | ForEach-Object { $sessHash[$_.Name] = $_.Value }
    $sessHash["job"] = "sft_s8_weighted_unsloth"
    $sessHash["sft_backend"] = "unsloth"
    $sessHash["sft_export"] = $false
    $sessHash["gate0_merged"] = "/workspace/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit"
    $sessHash["smoke_only"] = [bool]$SmokeOnly
    $sessHash["pinned_sha"] = $PinnedSha
    $sessHash["max_wall_hours"] = $MaxWallHours
    Save-SftSession $sessHash

    & "$PSScriptRoot\sft_wait_ssh.ps1" -TimeoutMinutes $TimeoutMinutes
    if ($LASTEXITCODE -ne 0) { throw "SSH wait failed" }

    & "$PSScriptRoot\sft_verify_mount.ps1"
    if ($LASTEXITCODE -ne 0) { throw "volume mount verify failed" }

    # HF token into .sft_env (private S8 merge).
    $hf = Get-HfToken
    $hfB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($hf))
    $smokeFlag = if ($SmokeOnly) { "1" } else { "0" }
    Invoke-WeightedSsh @"
set -euo pipefail
python3 - <<'PY'
import base64, pathlib
hf = base64.b64decode('$hfB64').decode('utf-8')
path = pathlib.Path('/workspace/.sft_env')
lines = [
    'export HF_TOKEN=' + repr(hf),
    'export HF_HOME=/workspace/hf_home',
    'export SFT_BACKEND=unsloth',
    'export SFT_SMOKE_ONLY=$smokeFlag',
    'export SFT_EXPORT=0',
]
path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
path.chmod(0o600)
print('SFT_ENV_OK backend=unsloth smoke_only=$smokeFlag')
PY
"@

    Sync-WeightedFromGit -PinnedSha $PinnedSha -DirtyOverrides $DirtyOverrides

    $launch = @"
set -euo pipefail
source /workspace/.sft_env 2>/dev/null || true
export SFT_BACKEND=unsloth
export SFT_SMOKE_ONLY=$smokeFlag
chmod +x /workspace/sft_remote_setup.sh /workspace/sft_remote_train_s8_weighted.sh /workspace/sft_setup_fail_watchdog.sh /workspace/sft_setup_markers.sh /workspace/sft_weighted_state_probe.sh
rm -f /workspace/sft_train.exit
if pgrep -f "[b]ash /workspace/sft_remote_train_s8_weighted.sh" >/dev/null 2>&1; then
  echo "sft_remote_train_s8_weighted.sh already running"
  exit 0
fi
: > /workspace/sft_setup.log
nohup bash /workspace/sft_remote_train_s8_weighted.sh > /workspace/sft_launch.log 2>&1 &
echo "LAUNCH_PID `$!"
sleep 5
if [ -f /workspace/sft_train.pid ]; then echo "SFT_TRAIN_PID `$(cat /workspace/sft_train.pid)"; fi
tail -n 40 /workspace/sft_launch.log || true
tail -n 20 /workspace/sft_setup.log || true
"@
    Invoke-WeightedSsh $launch
    Write-Host "Detached weighted Unsloth launch started (SFT_BACKEND=unsloth SFT_SMOKE_ONLY=$smokeFlag)."

    Write-Host "Walk-away gates to confirm in /workspace/sft_train.log (or setup/smoke for -SmokeOnly):"
    Write-Host "  SFT_OPEN_THEOLOGY=1"
    Write-Host "  RAG_PROMPT_OK / THEOLOGY_PROMPT_OK"
    Write-Host "  BASE_MODEL .../qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit"
    Write-Host "  SFT_BACKEND: unsloth   SFT_EXPORT=0"
    Write-Host "  SFT_OUTPUT_DIR: /workspace/sft_s8_weighted/adapter"
    Write-Host "  not Resuming from .../spurgeon_qa_lora_v2"
    if ($SmokeOnly) {
        Write-Host "  SMOKE_ONLY_DONE (then estimate s/step vs Vast PEFT ~90s)"
    }
}
catch {
    Invoke-DestroyOnFail ("weighted unsloth launch failed: " + $_.Exception.Message)
}

$script:WeightedFailStop = $null
$script:WeightedSuccessStop = $null

if ($StartMonitor) {
    Write-Host "Watching train until exit (max_wall_h=$MaxWallHours)."
    Write-Host ("loading_timeout_min={0} (extends while sft_setup.log advances; only until pidfile)" -f $LoadingTimeoutMinutes)
    $monitorStart = [datetime]::UtcNow
    $deadline = $monitorStart.AddHours($MaxWallHours)
    $loadingDeadline = $monitorStart.AddMinutes([Math]::Max(1, $LoadingTimeoutMinutes))
    $graceMinutes = 3
    $deadNeeded = 3
    $unknownDestroyMinutes = 10
    $sawRunning = $false
    $pidfileSeen = $false
    $deadStreak = 0
    $unknownSince = $null
    $lastSetupMtime = $null
    $idlePolls = 0
    while ([datetime]::UtcNow -lt $deadline) {
        $st = Get-WeightedTrainState
        if ($st.PidfileSeen) { $pidfileSeen = $true }
        $pastGrace = (([datetime]::UtcNow - $monitorStart).TotalMinutes -ge $graceMinutes)

        if ($st.State -eq "SETUP_FAILED" -or $st.State -eq "SMOKE_BEFORE_TRAIN_FAILED") {
            $failReason = $st.State
            if ($st.TriggerLine) { $failReason = "$($st.State) trigger_line=$($st.TriggerLine)" }
            $script:WeightedFailStop = $failReason
            Write-Warning ("[{0:u}] WEIGHTED_STATE={1} -- evidence then destroy" -f [datetime]::UtcNow, $failReason)
            Save-WeightedEvidence -Reason $failReason
            break
        }

        if ($st.State -eq "SMOKE_ONLY_DONE") {
            $script:WeightedSuccessStop = "SMOKE_ONLY_DONE"
            Write-Host ("[{0:u}] WEIGHTED_STATE=SMOKE_ONLY_DONE -- fetch then destroy" -f [datetime]::UtcNow)
            break
        }

        if ($st.State -eq "ALIVE") {
            $sawRunning = $true
            $deadStreak = 0
            $unknownSince = $null
            Write-Host ("[{0:u}] WEIGHTED_STATE=ALIVE" -f [datetime]::UtcNow)
        }
        elseif ($st.State -eq "DEAD") {
            $unknownSince = $null
            if ($pastGrace -and ($sawRunning -or $pidfileSeen)) {
                $deadStreak++
                Write-Host ("[{0:u}] WEIGHTED_STATE=DEAD streak={1}/{2}" -f [datetime]::UtcNow, $deadStreak, $deadNeeded)
                if ($deadStreak -ge $deadNeeded) {
                    Write-Host "Train DEAD for $deadNeeded consecutive polls after grace -- fetch then destroy"
                    break
                }
            }
            else {
                $deadStreak = 0
                Write-Host ("[{0:u}] WEIGHTED_STATE=DEAD (grace/loading; not counting)" -f [datetime]::UtcNow)
            }
        }
        else {
            if ($null -eq $unknownSince) { $unknownSince = [datetime]::UtcNow }
            $unkMin = ([datetime]::UtcNow - $unknownSince).TotalMinutes
            Write-Host ("[{0:u}] WEIGHTED_STATE=UNKNOWN ({1:N1}m)" -f [datetime]::UtcNow, $unkMin)
            if ($unkMin -ge $unknownDestroyMinutes) {
                Write-Warning "UNKNOWN for ~${unknownDestroyMinutes}m -- checking pod still exists"
                try {
                    $sess = Get-SftSession
                    $podId = [string]$sess.pod_id
                    $pod = Invoke-RunpodRestV1 -Method GET -Path "/pods/$podId"
                    if (-not $pod) {
                        Write-Warning "Pod gone -- fetch then destroy"
                        break
                    }
                    Write-Host "Pod still present; continuing polls"
                    $unknownSince = [datetime]::UtcNow
                }
                catch {
                    Write-Host "pod query ambiguous; continuing polls"
                    $unknownSince = [datetime]::UtcNow
                }
            }
        }

        if (-not $pidfileSeen) {
            $idlePolls++
            if ($st.SetupMtime -and $st.SetupMtime -ne "0" -and $st.SetupMtime -ne $lastSetupMtime) {
                $loadingDeadline = [datetime]::UtcNow.AddMinutes([Math]::Max(1, $LoadingTimeoutMinutes))
                $lastSetupMtime = $st.SetupMtime
                Write-Host ("setup log advanced (mtime={0}); loading deadline extended +{1}m" -f $st.SetupMtime, $LoadingTimeoutMinutes)
            }
            Write-Host ("[{0:u}] waiting for pidfile / setup (poll {1})" -f [datetime]::UtcNow, $idlePolls)
            if ([datetime]::UtcNow -ge $loadingDeadline) {
                Write-Warning ("Train never created pidfile within loading timeout (~{0}m) -- fetch logs and destroy" -f $LoadingTimeoutMinutes)
                break
            }
        }

        Start-Sleep -Seconds 60
    }
}
else {
    Write-Warning "CRITICAL: Launched without -StartMonitor."
    try { Stop-Transcript | Out-Null } catch { }
    exit 0
}

Write-Host "Fetching weighted adapter + logs into $ResultsDir ..."
$session = Get-SftSession
if ($session -and $session.ssh_host) {
    $sshTarget = Get-SftSshRemote $session
    $port = Get-SftSshPort $session
    $scpBase = @(
        "-i", $SshKey,
        "-P", "$port",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "LogLevel=ERROR"
    )
    $remotePaths = @(
        "/workspace/sft_s8_weighted",
        "/workspace/sft_setup.log",
        "/workspace/sft_launch.log",
        "/workspace/sft_smoke.log",
        "/workspace/sft_train.log",
        "/workspace/sft_pip_freeze.txt"
    )
    foreach ($rp in $remotePaths) {
        $prev = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            & scp @($scpBase + @("-r", "${sshTarget}:${rp}", $ResultsDir)) 2>$null
        }
        catch { }
        finally { $ErrorActionPreference = $prev }
    }
}

if ($script:WeightedFailStop) {
    Save-WeightedEvidence -Reason $script:WeightedFailStop
}
elseif ($script:WeightedSuccessStop) {
    Save-WeightedEvidence -Reason $script:WeightedSuccessStop
}
else {
    Save-WeightedEvidence -Reason "post-fetch-destroy"
}

Invoke-DestroyRunpodPod -Reason $(if ($script:WeightedFailStop) { $script:WeightedFailStop } elseif ($script:WeightedSuccessStop) { $script:WeightedSuccessStop } else { "monitor-complete" })

if ($script:WeightedFailStop) {
    Write-Warning ("No successful train after {0}. Evidence saved and pod destroyed." -f $script:WeightedFailStop)
    try { Stop-Transcript | Out-Null } catch { }
    exit 1
}

Write-Host "DONE. Fetch dir: $ResultsDir"
Write-Host "SFT_EXPORT=0 - no Hub until F gates. Vast PEFT remains the fallback path."
try { Stop-Transcript | Out-Null } catch { }
exit 0
