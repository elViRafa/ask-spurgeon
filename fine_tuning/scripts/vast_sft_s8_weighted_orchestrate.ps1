# Vast weighted SFT on S8 merged CPT: RAG mix + open-theology slice.
# Default: local readiness only. Does not rent and does not contact Vast.
# Forge runs -Go after operator go: rent, sync, train, fetch adapter, destroy.
# Do NOT call vast_orchestrate.ps1 (GATE-0) or vast_sft_s8_orchestrate.ps1 (RAG-only).
# Sync: pinned sparse-checkout on GPU; SCP only dirty overrides (-AllowDirtySync).
param(
    [switch]$Go,
    [string]$OfferId = "",
    [switch]$AllowLowCredit,
    [switch]$AllowDirtySync,
    [switch]$StartMonitor,
    [switch]$KeepInstance,
    [int]$DiskGb = 100,
    [int]$TimeoutMinutes = 45,
    [int]$GpuWaitMinutes = 15
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$FtRoot = Join-Path $RepoRoot "fine_tuning"
$SessionFile = Join-Path $FtRoot "kaggle\vast_sft_s8_weighted_session.json"
$ResultsDir = Join-Path $FtRoot "kaggle\vast_sft_s8_weighted"
$PlanPy = Join-Path $PSScriptRoot "sft_s8_weighted_plan.py"
$Label = "sft-s8-weighted"
$MaxWallHours = 10
$GitHubRepoUrl = "https://github.com/elViRafa/ask-spurgeon.git"
$SparseConePaths = @("fine_tuning/data", "fine_tuning/scripts")

# Repo-relative path -> remote /workspace path (train contract).
$WeightedSyncMap = @(
    @{ Rel = "fine_tuning/scripts/train_sft_sota.py"; Remote = "/workspace/train_sft_sota.py" }
    @{ Rel = "fine_tuning/scripts/sft_stop_token_utils.py"; Remote = "/workspace/sft_stop_token_utils.py" }
    @{ Rel = "fine_tuning/scripts/sft_remote_setup.sh"; Remote = "/workspace/sft_remote_setup.sh" }
    @{ Rel = "fine_tuning/scripts/sft_remote_train_s8_weighted.sh"; Remote = "/workspace/sft_remote_train_s8_weighted.sh" }
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

Write-Host "=== Vast SFT S8 weighted (RAG + open-theology) ==="
Write-Host "go=$Go start_monitor=$StartMonitor allow_dirty_sync=$AllowDirtySync (train only if -Go)"
Write-Host "session=$SessionFile"
Write-Host "results=$ResultsDir"

& $py $PlanPy
if ($LASTEXITCODE -ne 0) { throw "local readiness FAIL" }

$PinnedSha = Get-PinnedSha
$DirtyOverrides = @(Get-DirtyWeightedSyncOverrides)
Write-Host ""
Write-WeightedSyncBanner -PinnedSha $PinnedSha -DirtyOverrides $DirtyOverrides

if (-not $Go) {
    Write-Host ""
    Write-Host "DRY COMPLETE -- no instance rented, no download, no training started."
    Write-Host "No vastai, scp, or ssh calls were made."
    Write-Host "Sync on -Go: sparse-checkout at PINNED_SHA on GPU; SCP only dirty overrides (with -AllowDirtySync)."
    Write-Host "Base: rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit"
    Write-Host "Hub LoRA v2 06354dfc stays. SFT_EXPORT=0 until F gates."
    Write-Host "Output: /workspace/sft_s8_weighted/adapter"
    Write-Host "Forge rents only after Rafael says go:"
    Write-Host "  cd fine_tuning\scripts"
    Write-Host "  .\vast_sft_s8_weighted_orchestrate.ps1 -Go -StartMonitor"
    if ($DirtyOverrides.Count -gt 0 -and -not $AllowDirtySync) {
        Write-Host "READY with dirty sync paths -- push/commit or use -AllowDirtySync before -Go."
    }
    else {
        Write-Host "READY"
    }
    exit 0
}

if ($DirtyOverrides.Count -gt 0 -and -not $AllowDirtySync) {
    throw ("Sync paths dirty vs HEAD ($($DirtyOverrides.Count)). Commit/push, or pass -AllowDirtySync to SCP overrides after sparse-checkout. Dirty: " + (($DirtyOverrides | ForEach-Object { $_.Rel }) -join ", "))
}

# --- -Go only: vastai / ssh / scp below this line ---
$env:VAST_SESSION_FILE = $SessionFile
$env:VAST_LOCAL_RESULTS_DIR = $ResultsDir

. "$PSScriptRoot\vast_common.ps1"
$Script:DefaultLabel = $Label
$Script:DefaultDiskGb = $DiskGb
$Script:MaxWallHours = $MaxWallHours
$Script:StateFile = $SessionFile
$Script:LocalResultsDir = $ResultsDir

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $SessionFile -Parent) | Out-Null

$user = Invoke-VastaiJson -CliArgs @("show", "user")
$credit = $null
foreach ($k in @("credit", "credits", "balance", "account_credit")) {
    if ($null -ne $user.$k) { $credit = [double]$user.$k; break }
}
if ($null -eq $credit) { throw "Vast show user returned no credit field" }
Write-Host ("live_credit={0:N2}" -f $credit)
if ($credit -lt 5 -and -not $AllowLowCredit) {
    throw "Vast credit $credit is under `$5. Add funds, or retry with -AllowLowCredit."
}

Write-Host "Searching on-demand full RTX 4090 offers (quote only until create) ..."
Write-Host "Query: $SearchQuery"
$offers = Find-VastCheapestOffer -Query $SearchQuery -Limit 5
$best = $offers[0]
$bestId = $best.id
if (-not $bestId) { $bestId = $best.ask_contract_id }
$dph = $best.dph_total
if (-not $dph) { $dph = $best.dph }
$dph = [double]$dph
$quote = $dph * $MaxWallHours
Write-Host ("cheapest offer_id={0}  {1:N3}/hr  gpu={2}  quote_{3}h={4:N2}" -f $bestId, $dph, $best.gpu_name, $MaxWallHours, $quote)
if ($quote -gt $credit -and -not $AllowLowCredit) {
    throw ("Quoted cost {0:N2} ({1}h x {2:N3}/hr) exceeds credit {3:N2}. Top up, pass a cheaper -OfferId, or -AllowLowCredit." -f $quote, $MaxWallHours, $dph, $credit)
}
if (-not $OfferId) { $OfferId = [string]$bestId }

function Invoke-DestroyOnFail {
    param([string]$Reason)
    Write-Host "FAIL: $Reason - destroying instance to stop billing"
    try { & "$PSScriptRoot\vast_destroy.ps1" -Force } catch { Write-Warning $_.Exception.Message }
    throw $Reason
}

function Invoke-WeightedSsh([string]$Remote) {
    $session = Get-VastSession
    $sshArgs = (Get-VastSshArgs $session) + @((Get-VastSshRemote $session), $Remote)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & ssh @sshArgs
        $Script:LastRemoteExit = [int]$LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $prev
    }
    if ($Script:LastRemoteExit -ne 0) {
        throw "remote ssh failed exit=$($Script:LastRemoteExit)"
    }
}

function Copy-ToVastWeighted {
    param(
        [string]$Local,
        [string]$Remote,
        [switch]$GzipLarge
    )
    if (-not (Test-Path -LiteralPath $Local)) {
        throw "local file missing for scp: $Local"
    }
    $session = Get-VastSession
    $port = Get-VastSshPort $session
    $sshTarget = Get-VastSshRemote $session
    $sizeBytes = [double](Get-Item -LiteralPath $Local).Length
    $sizeMb = $sizeBytes / 1MB
    $useGzip = $GzipLarge -or ($Local -match 'qa_mix_train\.jsonl$' -and $sizeBytes -ge 5MB)
    $uploadLocal = $Local
    $uploadRemote = $Remote
    $gzTemp = $null
    if ($useGzip) {
        $gzTemp = Join-Path $env:TEMP ("vast_weighted_" + [guid]::NewGuid().ToString("n") + ".gz")
        Write-Host ("gzip {0:N1} MB -> {1}" -f $sizeMb, $gzTemp)
        $inStream = [System.IO.File]::OpenRead($Local)
        try {
            $outStream = [System.IO.File]::Create($gzTemp)
            try {
                $gzip = New-Object System.IO.Compression.GZipStream(
                    $outStream,
                    [System.IO.Compression.CompressionLevel]::Optimal
                )
                try { $inStream.CopyTo($gzip) }
                finally { $gzip.Dispose() }
            }
            finally { $outStream.Dispose() }
        }
        finally { $inStream.Dispose() }
        $uploadLocal = $gzTemp
        $uploadRemote = "$Remote.gz"
        $sizeBytes = [double](Get-Item -LiteralPath $gzTemp).Length
        $sizeMb = $sizeBytes / 1MB
        Write-Host ("gzipped size {0:N1} MB" -f $sizeMb)
    }

    $scpBase = @(
        "-i", $SshKey,
        "-P", "$port",
        "-C",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "LogLevel=ERROR",
        "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=10",
        "-o", "ConnectTimeout=20"
    )
    $maxAttempts = 3
    $minKbPerSec = 200.0
    $maxSecondsForLarge = 300.0
    $ok = $false
    $lastExit = -1
    for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
        Write-Host ("scp attempt {0}/{1}: {2} -> {3} ({4:N1} MB)" -f $attempt, $maxAttempts, $uploadLocal, $uploadRemote, $sizeMb)
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $prev = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            & scp @($scpBase + @($uploadLocal, "${sshTarget}:$uploadRemote"))
            $lastExit = [int]$LASTEXITCODE
        }
        finally {
            $ErrorActionPreference = $prev
        }
        $sw.Stop()
        $elapsed = [math]::Max(0.001, $sw.Elapsed.TotalSeconds)
        $kbPerSec = ($sizeBytes / 1024.0) / $elapsed
        Write-Host ("scp done exit={0} elapsed={1:N1}s speed={2:N0} KB/s" -f $lastExit, $elapsed, $kbPerSec)
        if ($lastExit -ne 0) {
            Write-Warning "scp failed exit=$lastExit (attempt $attempt)"
            Start-Sleep -Seconds (2 * $attempt)
            continue
        }
        if ($sizeBytes -ge 5MB) {
            if ($kbPerSec -lt $minKbPerSec) {
                if ($gzTemp -and (Test-Path -LiteralPath $gzTemp)) { Remove-Item -LiteralPath $gzTemp -Force -ErrorAction SilentlyContinue }
                throw ("scp too slow: {0:N0} KB/s < {1} KB/s for {2}" -f $kbPerSec, $minKbPerSec, $Local)
            }
            if ($elapsed -gt $maxSecondsForLarge -and $sizeBytes -ge 30MB) {
                if ($gzTemp -and (Test-Path -LiteralPath $gzTemp)) { Remove-Item -LiteralPath $gzTemp -Force -ErrorAction SilentlyContinue }
                throw ("scp exceeded {0:N0}s for large file {1} ({2:N1} MB)" -f $maxSecondsForLarge, $Local, $sizeMb)
            }
        }
        $ok = $true
        break
    }
    if (-not $ok) {
        if ($gzTemp -and (Test-Path -LiteralPath $gzTemp)) { Remove-Item -LiteralPath $gzTemp -Force -ErrorAction SilentlyContinue }
        throw "scp failed after $maxAttempts attempts: $Local -> $Remote (last exit=$lastExit)"
    }
    if ($useGzip) {
        Invoke-WeightedSsh "gunzip -f '$uploadRemote' && test -f '$Remote'"
        if ($gzTemp -and (Test-Path -LiteralPath $gzTemp)) { Remove-Item -LiteralPath $gzTemp -Force -ErrorAction SilentlyContinue }
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
    # Expand only PINNED_SHA / URL / cone from PowerShell; bash vars use `$...
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
test -f "`$SRC/fine_tuning/data/qa_mix_val.jsonl"
test -f "`$SRC/fine_tuning/data/qa_open_theology/sft/open_theology_train.jsonl"
test -f "`$SRC/fine_tuning/scripts/train_sft_sota.py"
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
git -C "`$SRC" show HEAD:config.py > /workspace/config.py
chmod +x /workspace/sft_remote_setup.sh /workspace/sft_remote_train_s8_weighted.sh
test -s /workspace/spurgeon-qa-mix-v1/qa_mix_train.jsonl
test -s /workspace/config.py
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
            Copy-ToVastWeighted $d.Local $d.Remote
        }
    }
    Invoke-WeightedSsh "chmod +x /workspace/sft_remote_setup.sh /workspace/sft_remote_train_s8_weighted.sh && test -f /workspace/spurgeon-qa-mix-v1/qa_mix_train.jsonl && test -f /workspace/qa_open_theology/sft/open_theology_train.jsonl"
    Write-Host "Sync complete (sparse + overrides)."
}

Write-Host ""
Write-Host "GO: renting Vast GPU for weighted SFT"
$provArgs = @{
    DiskGb = $DiskGb
    Label  = $Label
    Force  = $true
    OfferId = $OfferId
}
& "$PSScriptRoot\vast_provision.ps1" @provArgs
if ($LASTEXITCODE -ne 0) { throw "provision failed" }

& "$PSScriptRoot\vast_wait_ssh.ps1" -TimeoutMinutes $TimeoutMinutes
if ($LASTEXITCODE -ne 0) { Invoke-DestroyOnFail "SSH wait failed" }

$gpuDeadline = [datetime]::UtcNow.AddMinutes($GpuWaitMinutes)
$gpuOk = $false
while ([datetime]::UtcNow -lt $gpuDeadline) {
    & "$PSScriptRoot\vast_verify_gpu.ps1"
    if ($LASTEXITCODE -eq 0) { $gpuOk = $true; break }
    Write-Host "Waiting for nvidia-smi ..."
    Start-Sleep -Seconds 20
}
if (-not $gpuOk) { Invoke-DestroyOnFail "nvidia-smi never became ready" }

& "$PSScriptRoot\vast_inject_hf_token.ps1"
if ($LASTEXITCODE -ne 0) { Invoke-DestroyOnFail "HF token inject failed" }

try {
    Sync-WeightedFromGit -PinnedSha $PinnedSha -DirtyOverrides $DirtyOverrides
}
catch {
    Invoke-DestroyOnFail ("weighted sparse sync failed: " + $_.Exception.Message)
}

$launch = @'
set -euo pipefail
source /workspace/.sft_env 2>/dev/null || true
chmod +x /workspace/sft_remote_setup.sh /workspace/sft_remote_train_s8_weighted.sh
if pgrep -f "[b]ash /workspace/sft_remote_train_s8_weighted.sh" >/dev/null 2>&1; then
  echo "sft_remote_train_s8_weighted.sh already running"
  pgrep -af "[b]ash /workspace/sft_remote_train_s8_weighted.sh" || true
  exit 0
fi
nohup bash /workspace/sft_remote_train_s8_weighted.sh > /workspace/sft_launch.log 2>&1 &
echo "LAUNCH_PID $!"
sleep 5
tail -n 40 /workspace/sft_launch.log || true
'@
Invoke-WeightedSsh $launch
Write-Host "Detached weighted launch started."

Write-Host "Walk-away gates to confirm in /workspace/sft_train.log:"
Write-Host "  SFT_OPEN_THEOLOGY=1"
Write-Host "  RAG_PROMPT_OK / THEOLOGY_PROMPT_OK"
Write-Host "  BASE_MODEL .../qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit"
Write-Host "  SFT_BACKEND: peft   SFT_EXPORT=0"
Write-Host "  SFT_OUTPUT_DIR: /workspace/sft_s8_weighted/adapter"
Write-Host "  not Resuming from .../spurgeon_qa_lora_v2"

function Test-WeightedTrainRunning {
    $session = Get-VastSession
    if (-not $session -or -not $session.ssh_host) { return $false }
    $sshArgs = (Get-VastSshArgs $session) + @(
        (Get-VastSshRemote $session),
        "pgrep -af 'python3 -u /workspace/train_sft_sota.py' || true"
    )
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $out = & ssh @sshArgs 2>&1 | Out-String
    }
    finally {
        $ErrorActionPreference = $prev
    }
    foreach ($line in ($out -split "`n")) {
        if ($line -match "train_sft_sota\.py" -and $line -notmatch "pgrep") { return $true }
    }
    return $false
}

if ($StartMonitor) {
    Write-Host "Watching train until exit (max_wall_h=$MaxWallHours). Does not use GATE-0 vast_monitor paths."
    $deadline = [datetime]::UtcNow.AddHours($MaxWallHours)
    $sawRunning = $false
    $idlePolls = 0
    while ([datetime]::UtcNow -lt $deadline) {
        $running = Test-WeightedTrainRunning
        if ($running) {
            $sawRunning = $true
            $idlePolls = 0
            Write-Host ("[{0:u}] training still running" -f [datetime]::UtcNow)
        }
        else {
            if ($sawRunning) {
                Write-Host "Train process gone after running -- fetch then destroy"
                break
            }
            $idlePolls++
            Write-Host ("[{0:u}] waiting for train start (poll {1})" -f [datetime]::UtcNow, $idlePolls)
            if ($idlePolls -ge 8) {
                Write-Warning "Train never started after ~40m -- fetch logs and destroy"
                break
            }
        }
        Start-Sleep -Seconds 300
    }
}
else {
    Write-Host "Launched without -StartMonitor. Fetch/destroy when train finishes:"
    Write-Host "  .\vast_sft_s8_weighted_orchestrate.ps1 -Go -StartMonitor"
    Write-Host "  (or re-run fetch by hand from the session SSH)"
    exit 0
}

Write-Host "Fetching weighted adapter + logs into $ResultsDir ..."
$session = Get-VastSession
if ($session -and $session.ssh_host) {
    $sshTarget = Get-VastSshRemote $session
    $port = Get-VastSshPort $session
    $scpBase = @(
        "-i", $SshKey,
        "-P", "$port",
        "-o", "StrictHostKeyChecking=accept-new"
    )
    $remotePaths = @(
        "/workspace/sft_s8_weighted",
        "/workspace/sft_train.log",
        "/workspace/sft_launch.log",
        "/workspace/sft_run_config.json"
    )
    foreach ($remotePath in $remotePaths) {
        $name = Split-Path $remotePath -Leaf
        $dest = Join-Path $ResultsDir $name
        Write-Host "Fetching $remotePath ..."
        & scp @($scpBase + @("-r", "${sshTarget}:$remotePath", $dest))
        if ($LASTEXITCODE -ne 0) { Write-Host "  (not present yet)" }
    }
}
else {
    Write-Warning "No SSH session for fetch"
}

$adapterOk = Test-Path (Join-Path $ResultsDir "sft_s8_weighted\adapter\adapter_config.json")
if (-not $adapterOk) {
    $adapterOk = Test-Path (Join-Path $ResultsDir "adapter\adapter_config.json")
}
Write-Host ("fetch_adapter_ok={0}" -f $adapterOk)

if (-not $KeepInstance) {
    Write-Host "Destroying instance after fetch ..."
    & "$PSScriptRoot\vast_destroy.ps1" -Force
}

if (-not $adapterOk) {
    throw "Weighted adapter missing after fetch. Check $ResultsDir and sft_train.log before another go."
}

Write-Host "WEIGHTED SFT COMPLETE -- artifacts in $ResultsDir"
Write-Host "No Hub upload. Score RAG with sft_export_if_gates.ps1 later."
exit 0
