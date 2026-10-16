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
    [int]$GpuWaitMinutes = 15,
    # Max wait for sft_train.pid after launch (setup + model load). Extends while sft_setup.log advances.
    [int]$LoadingTimeoutMinutes = 20
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

# -Go without a local monitor left run3 billing ~30m after setup exit 1.
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

# Repo-relative path -> remote /workspace path (train contract).
$WeightedSyncMap = @(
    @{ Rel = "fine_tuning/scripts/train_sft_sota.py"; Remote = "/workspace/train_sft_sota.py" }
    @{ Rel = "fine_tuning/scripts/sft_stop_token_utils.py"; Remote = "/workspace/sft_stop_token_utils.py" }
    @{ Rel = "fine_tuning/scripts/sft_remote_setup.sh"; Remote = "/workspace/sft_remote_setup.sh" }
    @{ Rel = "fine_tuning/scripts/sft_remote_train_s8_weighted.sh"; Remote = "/workspace/sft_remote_train_s8_weighted.sh" }
    @{ Rel = "fine_tuning/scripts/sft_setup_fail_watchdog.sh"; Remote = "/workspace/sft_setup_fail_watchdog.sh" }
    @{ Rel = "fine_tuning/scripts/sft_setup_markers.sh"; Remote = "/workspace/sft_setup_markers.sh" }
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
    try { Stop-Transcript | Out-Null } catch { }
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

function Save-WeightedEvidence {
    param([string]$Reason = "")
    # Diagnostics before destroy. Asserts files exist; scp-falls back for logs.
    # Never throws (destroy must proceed); writes status.txt with ok/fail.
    # Only prints "evidence saved" when a real non-empty payload was copied.
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $evDir = Join-Path $ResultsDir "evidence_$stamp"
    $statusLines = New-Object System.Collections.Generic.List[string]
    $statusLines.Add("reason=$Reason")
    $statusLines.Add("utc=$((Get-Date).ToUniversalTime().ToString('o'))")
    $statusLines.Add("ev_dir=$evDir")
    try {
        New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
        New-Item -ItemType Directory -Force -Path $evDir | Out-Null
        @(
            "reason=$Reason"
            "utc=$((Get-Date).ToUniversalTime().ToString('o'))"
        ) | Set-Content -LiteralPath (Join-Path $evDir "meta.txt") -Encoding utf8

        $session = $null
        try { $session = Get-VastSession } catch { $session = $null }
        $sshOk = $false
        $scpOk = $false
        $copiedBytes = 0
        if ($session -and $session.ssh_host) {
            $cap = @'
set +e
echo "===DMESG==="
dmesg 2>/dev/null | tail -n 200
echo "===FREE==="
free -h 2>&1
echo "===NVIDIA==="
nvidia-smi 2>&1
echo "===SFT_TRAIN_TAIL==="
tail -n 200 /workspace/sft_train.log 2>/dev/null || true
echo "===SFT_LAUNCH_TAIL==="
tail -n 200 /workspace/sft_launch.log 2>/dev/null || true
echo "===SFT_SETUP_TAIL==="
tail -n 200 /workspace/sft_setup.log 2>/dev/null || true
echo "===SFT_SMOKE_TAIL==="
tail -n 200 /workspace/sft_smoke.log 2>/dev/null || true
echo "===SFT_WATCHDOG_TAIL==="
tail -n 120 /workspace/sft_watchdog.log 2>/dev/null || true
echo "===FAIL_EVIDENCE==="
ls -la /workspace/sft_fail_evidence 2>/dev/null || true
tail -n 80 /workspace/sft_fail_evidence/capture.txt 2>/dev/null || true
echo "===PIP_FREEZE_HEAD==="
head -n 80 /workspace/sft_pip_freeze.txt 2>/dev/null || true
echo "===PID_EXIT==="
cat /workspace/sft_train.pid 2>/dev/null || true
cat /workspace/sft_train.exit 2>/dev/null || true
echo "===EV_DONE==="
'@
            $cap = $cap -replace "`r", ""
            for ($attempt = 1; $attempt -le 3; $attempt++) {
                try {
                    $sshArgs = (Get-VastSshArgs $session) + @((Get-VastSshRemote $session), $cap)
                    $prev = $ErrorActionPreference
                    $ErrorActionPreference = "Continue"
                    try {
                        $out = & ssh @sshArgs 2>&1 | Out-String
                        $sx = [int]$LASTEXITCODE
                    }
                    finally {
                        $ErrorActionPreference = $prev
                    }
                    if (($sx -eq 0 -or ($out -match "EV_DONE")) -and ($out -match "EV_DONE") -and ($out.Length -gt 80)) {
                        $capPath = Join-Path $evDir "capture.txt"
                        $out | Set-Content -LiteralPath $capPath -Encoding utf8
                        if ((Test-Path -LiteralPath $capPath) -and ((Get-Item -LiteralPath $capPath).Length -gt 80)) {
                            $sshOk = $true
                            $copiedBytes += (Get-Item -LiteralPath $capPath).Length
                            break
                        }
                    }
                }
                catch {
                    Write-Warning ("evidence ssh attempt {0} failed: {1}" -f $attempt, $_.Exception.Message)
                }
                Start-Sleep -Seconds (2 * $attempt)
            }

            # SCP: always copy remote logs / fail_evidence (real files), not meta-only dirs.
            try {
                $sshTarget = Get-VastSshRemote $session
                $port = Get-VastSshPort $session
                $scpBase = @(
                    "-i", $SshKey,
                    "-P", "$port",
                    "-o", "StrictHostKeyChecking=accept-new",
                    "-o", "LogLevel=ERROR"
                )
                $remoteLogs = @(
                    "/workspace/sft_train.log",
                    "/workspace/sft_launch.log",
                    "/workspace/sft_setup.log",
                    "/workspace/sft_smoke.log",
                    "/workspace/sft_watchdog.log",
                    "/workspace/sft_pip_freeze.txt",
                    "/workspace/sft_train.pid",
                    "/workspace/sft_train.exit",
                    "/workspace/sft_smoke_fail/status.txt",
                    "/workspace/sft_fail_evidence/capture.txt",
                    "/workspace/sft_fail_evidence/status.txt",
                    "/workspace/sft_fail_evidence/sft_setup.log"
                )
                foreach ($remotePath in $remoteLogs) {
                    $leaf = Split-Path $remotePath -Leaf
                    $dest = Join-Path $evDir ("scp_" + $leaf)
                    $prev = $ErrorActionPreference
                    $ErrorActionPreference = "Continue"
                    try {
                        & scp @($scpBase + @("${sshTarget}:$remotePath", $dest)) 2>$null
                        $sx = [int]$LASTEXITCODE
                    }
                    finally {
                        $ErrorActionPreference = $prev
                    }
                    if ($sx -eq 0 -and (Test-Path -LiteralPath $dest) -and ((Get-Item -LiteralPath $dest).Length -gt 0)) {
                        $scpOk = $true
                        $copiedBytes += (Get-Item -LiteralPath $dest).Length
                    }
                    elseif (Test-Path -LiteralPath $dest) {
                        # Drop zero-byte failed scp placeholders.
                        Remove-Item -LiteralPath $dest -Force -ErrorAction SilentlyContinue
                    }
                }
            }
            catch {
                Write-Warning ("evidence scp fallback failed: {0}" -f $_.Exception.Message)
                $statusLines.Add("scp_error=$($_.Exception.Message)")
            }
        }
        if (-not $sshOk -and -not $scpOk) {
            try {
                $id = if ($session -and $session.instance_id) { [string]$session.instance_id } else { "" }
                if ($id) {
                    $logs = Invoke-Vastai -CliArgs @("logs", $id)
                    $logsText = if ($null -eq $logs) { "" } else { [string]$logs }
                    # Only keep vastai logs when they look like real container output.
                    if ($logsText.Length -gt 120 -and $logsText -notmatch "(?i)No such container") {
                        $logsText | Set-Content -LiteralPath (Join-Path $evDir "vastai_logs.txt") -Encoding utf8
                        $copiedBytes += (Get-Item -LiteralPath (Join-Path $evDir "vastai_logs.txt")).Length
                    }
                    else {
                        $statusLines.Add("vastai_logs_skipped=too_short_or_missing_container")
                    }
                }
                else {
                    $statusLines.Add("vastai_logs_skipped=no_instance_id")
                }
            }
            catch {
                Write-Warning ("vastai logs fallback failed: {0}" -f $_.Exception.Message)
                $statusLines.Add("vastai_logs_error=$($_.Exception.Message)")
            }
        }

        $listingPath = Join-Path $evDir "listing.txt"
        $listing = New-Object System.Collections.Generic.List[string]
        if (Test-Path -LiteralPath $evDir) {
            Get-ChildItem -LiteralPath $evDir -File | ForEach-Object {
                [void]$listing.Add(("{0}`t{1}" -f $_.Name, $_.Length))
            }
        }
        if ($listing.Count -eq 0) {
            [void]$listing.Add("(empty)")
        }
        $listing | Set-Content -LiteralPath $listingPath -Encoding utf8

        $metaOk = (Test-Path -LiteralPath (Join-Path $evDir "meta.txt"))
        $listOk = (Test-Path -LiteralPath $listingPath) -and ((Get-Item -LiteralPath $listingPath).Length -gt 0)
        # Real payload = capture with EV_DONE, or any non-empty scp_* log — not meta/listing alone,
        # and not a tiny/error-only vastai_logs.txt.
        $payloadOk = $false
        $capCheck = Join-Path $evDir "capture.txt"
        if ((Test-Path -LiteralPath $capCheck) -and ((Get-Item -LiteralPath $capCheck).Length -gt 80)) {
            $capText = Get-Content -LiteralPath $capCheck -Raw -ErrorAction SilentlyContinue
            if ($capText -match "EV_DONE") { $payloadOk = $true }
        }
        if (-not $payloadOk) {
            foreach ($f in (Get-ChildItem -LiteralPath $evDir -File -Filter "scp_*" -ErrorAction SilentlyContinue)) {
                if ($f.Length -gt 0) { $payloadOk = $true; break }
            }
        }
        $vastaiPath = Join-Path $evDir "vastai_logs.txt"
        if (-not $payloadOk -and (Test-Path -LiteralPath $vastaiPath)) {
            $vl = Get-Item -LiteralPath $vastaiPath
            if ($vl.Length -gt 120) {
                $vlText = Get-Content -LiteralPath $vastaiPath -Raw -ErrorAction SilentlyContinue
                if ($vlText -and $vlText -notmatch "(?i)No such container") { $payloadOk = $true }
            }
        }
        $requiredOk = $metaOk -and $listOk -and $payloadOk
        $statusLines.Add("ssh_capture_ok=$sshOk")
        $statusLines.Add("scp_fallback_ok=$scpOk")
        $statusLines.Add("copied_bytes=$copiedBytes")
        $statusLines.Add("meta_ok=$metaOk")
        $statusLines.Add("listing_ok=$listOk")
        $statusLines.Add("payload_ok=$payloadOk")
        $statusLines.Add("evidence_ok=$requiredOk")
        $statusLines.Add("files:")
        foreach ($line in $listing) { [void]$statusLines.Add([string]$line) }
        $statusPath = Join-Path $evDir "status.txt"
        $statusLines | Set-Content -LiteralPath $statusPath -Encoding utf8

        if ($requiredOk) {
            Write-Host "evidence saved: $evDir"
        }
        else {
            Write-Warning ("evidence INCOMPLETE (nothing real copied): {0} -- see status.txt" -f $evDir)
        }
        # Assert after write -- surface empty-folder regressions in the log.
        if (-not (Test-Path -LiteralPath $statusPath)) {
            Write-Warning "ASSERT FAIL: status.txt missing after Save-WeightedEvidence"
        }
        if (-not (Test-Path -LiteralPath $listingPath)) {
            Write-Warning "ASSERT FAIL: listing.txt missing after Save-WeightedEvidence"
        }
        if (-not $payloadOk) {
            Write-Warning "ASSERT FAIL: no non-empty evidence payload file in $evDir"
        }
    }
    catch {
        Write-Warning ("Save-WeightedEvidence failed (non-fatal): {0}" -f $_.Exception.Message)
        try {
            New-Item -ItemType Directory -Force -Path $evDir | Out-Null
            $statusLines.Add("exception=$($_.Exception.Message)")
            $statusLines.Add("evidence_ok=False")
            $statusLines | Set-Content -LiteralPath (Join-Path $evDir "status.txt") -Encoding utf8
        }
        catch { }
    }
}

function Invoke-DestroyOnFail {
    param([string]$Reason)
    Write-Host "FAIL: $Reason - destroying instance to stop billing"
    Save-WeightedEvidence -Reason $Reason
    try { & "$PSScriptRoot\vast_destroy.ps1" -Force } catch { Write-Warning $_.Exception.Message }
    try { Stop-Transcript | Out-Null } catch { }
    throw $Reason
}

function Invoke-WeightedSsh([string]$Remote) {
    # Windows PowerShell here-strings keep CRLF; bash on the GPU treats \r as part of
    # the command (e.g. $'set -euo pipefail\r'). Strip every CR before ssh.
    $Remote = $Remote -replace "`r", ""
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
cp "`$SRC/fine_tuning/scripts/sft_setup_fail_watchdog.sh" /workspace/sft_setup_fail_watchdog.sh
cp "`$SRC/fine_tuning/scripts/sft_setup_markers.sh" /workspace/sft_setup_markers.sh
cp "`$SRC/fine_tuning/scripts/sft_gate0_sep6_constraints.txt" /workspace/sft_gate0_sep6_constraints.txt
git -C "`$SRC" show HEAD:config.py > /workspace/config.py
chmod +x /workspace/sft_remote_setup.sh /workspace/sft_remote_train_s8_weighted.sh /workspace/sft_setup_fail_watchdog.sh /workspace/sft_setup_markers.sh
test -s /workspace/spurgeon-qa-mix-v1/qa_mix_train.jsonl
test -s /workspace/config.py
test -s /workspace/train_sft_sota.py
test -s /workspace/sft_gate0_sep6_constraints.txt
test -s /workspace/sft_setup_fail_watchdog.sh
test -s /workspace/sft_setup_markers.sh
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
    Invoke-WeightedSsh "chmod +x /workspace/sft_remote_setup.sh /workspace/sft_remote_train_s8_weighted.sh /workspace/sft_setup_fail_watchdog.sh /workspace/sft_setup_markers.sh && test -f /workspace/spurgeon-qa-mix-v1/qa_mix_train.jsonl && test -f /workspace/qa_open_theology/sft/open_theology_train.jsonl && test -f /workspace/sft_setup_markers.sh"
    Write-Host "Sync complete (sparse + overrides)."
}

Write-Host ""
Write-Host "GO: renting Vast GPU for weighted SFT"
try {
    $provArgs = @{
        DiskGb = $DiskGb
        Label  = $Label
        Force  = $true
        OfferId = $OfferId
    }
    & "$PSScriptRoot\vast_provision.ps1" @provArgs
    if ($LASTEXITCODE -ne 0) { throw "provision failed" }

    & "$PSScriptRoot\vast_wait_ssh.ps1" -TimeoutMinutes $TimeoutMinutes
    if ($LASTEXITCODE -ne 0) { throw "SSH wait failed" }

    $gpuDeadline = [datetime]::UtcNow.AddMinutes($GpuWaitMinutes)
    $gpuOk = $false
    while ([datetime]::UtcNow -lt $gpuDeadline) {
        & "$PSScriptRoot\vast_verify_gpu.ps1"
        if ($LASTEXITCODE -eq 0) { $gpuOk = $true; break }
        Write-Host "Waiting for nvidia-smi ..."
        Start-Sleep -Seconds 20
    }
    if (-not $gpuOk) { throw "nvidia-smi never became ready" }

    & "$PSScriptRoot\vast_inject_hf_token.ps1"
    if ($LASTEXITCODE -ne 0) { throw "HF token inject failed" }

    Sync-WeightedFromGit -PinnedSha $PinnedSha -DirtyOverrides $DirtyOverrides

    # Inject watchdog creds (never echoed) + start detached self-destroy on setup fail.
    $sessionForWatch = Get-VastSession
    $watchInstanceId = [string]$sessionForWatch.instance_id
    $watchKey = Get-VastApiKey
    $watchKeyB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($watchKey))
    $watchIdB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($watchInstanceId))
    $launch = @"
set -euo pipefail
source /workspace/.sft_env 2>/dev/null || true
chmod +x /workspace/sft_remote_setup.sh /workspace/sft_remote_train_s8_weighted.sh /workspace/sft_setup_fail_watchdog.sh /workspace/sft_setup_markers.sh
rm -f /workspace/sft_train.exit /workspace/sft_watchdog_destroyed.marker
python3 - <<'PY'
import base64, pathlib
key = base64.b64decode('$watchKeyB64').decode('utf-8')
iid = base64.b64decode('$watchIdB64').decode('utf-8')
path = pathlib.Path('/workspace/.sft_watchdog_env')
path.write_text(
    'export VAST_API_KEY=' + repr(key) + '\n'
    'export VAST_INSTANCE_ID=' + repr(iid) + '\n',
    encoding='utf-8',
)
path.chmod(0o600)
print('WATCHDOG_ENV_OK')
PY
if pgrep -f "[b]ash /workspace/sft_remote_train_s8_weighted.sh" >/dev/null 2>&1; then
  echo "sft_remote_train_s8_weighted.sh already running"
  pgrep -af "[b]ash /workspace/sft_remote_train_s8_weighted.sh" || true
  if [ -f /workspace/sft_train.pid ]; then echo "EXISTING_PID `$(cat /workspace/sft_train.pid)"; fi
  exit 0
fi
: > /workspace/sft_setup.log
nohup bash /workspace/sft_setup_fail_watchdog.sh >> /workspace/sft_watchdog.log 2>&1 &
echo "WATCHDOG_PID `$!"
nohup bash /workspace/sft_remote_train_s8_weighted.sh > /workspace/sft_launch.log 2>&1 &
echo "LAUNCH_PID `$!"
sleep 5
if [ -f /workspace/sft_train.pid ]; then echo "SFT_TRAIN_PID `$(cat /workspace/sft_train.pid)"; fi
tail -n 40 /workspace/sft_launch.log || true
tail -n 20 /workspace/sft_setup.log || true
"@
    Invoke-WeightedSsh $launch
    Write-Host "Detached weighted launch + setup-fail watchdog started."

    Write-Host "Walk-away gates to confirm in /workspace/sft_train.log:"
    Write-Host "  SFT_OPEN_THEOLOGY=1"
    Write-Host "  RAG_PROMPT_OK / THEOLOGY_PROMPT_OK"
    Write-Host "  BASE_MODEL .../qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit"
    Write-Host "  SFT_BACKEND: peft   SFT_EXPORT=0"
    Write-Host "  SFT_OUTPUT_DIR: /workspace/sft_s8_weighted/adapter"
    Write-Host "  not Resuming from .../spurgeon_qa_lora_v2"
}
catch {
    Invoke-DestroyOnFail ("weighted launch failed: " + $_.Exception.Message)
}

function Get-WeightedTrainState {
    # Returns ALIVE / DEAD / UNKNOWN / SETUP_FAILED / SMOKE_BEFORE_TRAIN_FAILED.
    # SSH errors are UNKNOWN, never "gone". Fail markers break the monitor immediately.
    $result = [pscustomobject]@{
        State       = "UNKNOWN"
        PidfileSeen = $false
        SetupMtime  = $null
        SetupSize   = $null
        FailMarker  = $null
        Raw         = ""
    }
    $session = Get-VastSession
    if (-not $session -or -not $session.ssh_host) {
        return $result
    }
    $remote = @'
set +e
PIDFILE=/workspace/sft_train.pid
EXITFILE=/workspace/sft_train.exit
SETUPLOG=/workspace/sft_setup.log
LAUNCHLOG=/workspace/sft_launch.log
SMOKELOG=/workspace/sft_smoke.log
if [ -f "$SETUPLOG" ]; then
  echo "SETUP_MTIME=$(stat -c %Y "$SETUPLOG" 2>/dev/null || echo 0)"
  echo "SETUP_SIZE=$(wc -c < "$SETUPLOG" | tr -d ' \n')"
else
  echo "SETUP_MTIME=0"
  echo "SETUP_SIZE=0"
fi
for f in "$SETUPLOG" "$LAUNCHLOG" "$SMOKELOG"; do
  if [ -f "$f" ] && grep -q "SMOKE_BEFORE_TRAIN_FAILED" "$f" 2>/dev/null; then
    echo "FAIL_MARKER=SMOKE_BEFORE_TRAIN_FAILED"
    echo "WEIGHTED_STATE=SMOKE_BEFORE_TRAIN_FAILED"
    exit 0
  fi
done
# SETUP_FAILED gating: reason= always, or bare fail only after last SETUP_PINS_OK.
# Shared logic in /workspace/sft_setup_markers.sh (no line-number threshold).
if [ -f /workspace/sft_setup_markers.sh ]; then
  # shellcheck disable=SC1091
  . /workspace/sft_setup_markers.sh
else
  actionable_setup_failed_in() {
    local f="$1"
    [ -f "$f" ] || return 1
    grep -q "SETUP_FAILED" "$f" 2>/dev/null || return 1
    if grep -qE "SETUP_FAILED[[:space:]]+line=[0-9]+[[:space:]]+reason=" "$f" 2>/dev/null; then
      return 0
    fi
    local pins_line=0 i=0 line
    while IFS= read -r line || [ -n "$line" ]; do
      i=$((i + 1))
      case "$line" in
        *SETUP_PINS_OK*|*SETUP_PHASE=pins_ok*) pins_line=$i ;;
      esac
      if [ "$pins_line" -gt 0 ] && [ "$i" -gt "$pins_line" ] && echo "$line" | grep -q "SETUP_FAILED"; then
        return 0
      fi
    done < "$f"
    return 1
  }
fi
for f in "$SETUPLOG" "$LAUNCHLOG"; do
  if actionable_setup_failed_in "$f"; then
    echo "FAIL_MARKER=SETUP_FAILED"
    echo "WEIGHTED_STATE=SETUP_FAILED"
    exit 0
  fi
done
if [ -f "$PIDFILE" ]; then
  echo "PIDFILE=1"
  pid=$(tr -d ' \n\r' < "$PIDFILE")
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    echo "WEIGHTED_STATE=ALIVE"
    exit 0
  fi
else
  echo "PIDFILE=0"
fi
if [ -f "$EXITFILE" ]; then
  echo "WEIGHTED_STATE=DEAD"
  exit 0
fi
if pgrep -f "[b]ash /workspace/sft_remote_train_s8_weighted.sh" >/dev/null 2>&1 \
   || pgrep -f "[t]rain_sft_sota.py" >/dev/null 2>&1; then
  echo "WEIGHTED_STATE=ALIVE"
  exit 0
fi
if [ ! -f "$PIDFILE" ]; then
  echo "WEIGHTED_STATE=UNKNOWN"
  exit 0
fi
if [ -f "$SETUPLOG" ]; then
  now=$(date +%s)
  mtime=$(stat -c %Y "$SETUPLOG" 2>/dev/null || echo 0)
  age=$((now - mtime))
  if [ "$age" -lt 180 ]; then
    echo "WEIGHTED_STATE=UNKNOWN"
    exit 0
  fi
fi
echo "WEIGHTED_STATE=DEAD"
'@
    $remote = $remote -replace "`r", ""
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $sshArgs = (Get-VastSshArgs $session) + @((Get-VastSshRemote $session), $remote)
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
    if ($out -match "FAIL_MARKER=(\S+)") { $result.FailMarker = $Matches[1] }
    if ($out -match "WEIGHTED_STATE=SETUP_FAILED") {
        $result.State = "SETUP_FAILED"
    }
    elseif ($out -match "WEIGHTED_STATE=SMOKE_BEFORE_TRAIN_FAILED") {
        $result.State = "SMOKE_BEFORE_TRAIN_FAILED"
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

function Test-VastInstanceStillPresent {
    # After sustained UNKNOWN, ask Vast whether the instance still exists.
    # Returns $true if present, $false if gone / query says missing, $null if query failed ambiguously.
    try {
        $session = Get-VastSession
        if (-not $session -or -not $session.instance_id) { return $false }
        $id = [string]$session.instance_id
        $prev = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            $text = Invoke-Vastai -CliArgs @("show", "instance", $id)
        }
        finally {
            $ErrorActionPreference = $prev
        }
        if (-not $text) { return $false }
        if ($text -match "(?i)not found|no such|does not exist|unknown instance") { return $false }
        if ($text -match [regex]::Escape($id)) { return $true }
        return $true
    }
    catch {
        Write-Warning ("vastai show instance failed: {0}" -f $_.Exception.Message)
        return $null
    }
}

if ($StartMonitor) {
    Write-Host "Watching train until exit (max_wall_h=$MaxWallHours). Does not use GATE-0 vast_monitor paths."
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

        # Break fast on setup/smoke failure markers (evidence before destroy).
        if ($st.State -eq "SETUP_FAILED" -or $st.State -eq "SMOKE_BEFORE_TRAIN_FAILED") {
            Write-Warning ("[{0:u}] WEIGHTED_STATE={1} -- evidence then destroy" -f [datetime]::UtcNow, $st.State)
            Save-WeightedEvidence -Reason $st.State
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
            # UNKNOWN: never treat as gone; after ~10 min query vastai show instance
            if ($null -eq $unknownSince) { $unknownSince = [datetime]::UtcNow }
            $unkMin = ([datetime]::UtcNow - $unknownSince).TotalMinutes
            Write-Host ("[{0:u}] WEIGHTED_STATE=UNKNOWN ({1:N1}m)" -f [datetime]::UtcNow, $unkMin)
            if ($unkMin -ge $unknownDestroyMinutes) {
                Write-Warning "UNKNOWN for ~${unknownDestroyMinutes}m -- querying vastai show instance"
                $present = Test-VastInstanceStillPresent
                if ($present -eq $false) {
                    Write-Warning "Instance gone according to vastai -- fetch then destroy"
                    break
                }
                if ($present -eq $true) {
                    Write-Host "Instance still present; continuing polls (SSH flaps are not destroy)"
                    $unknownSince = [datetime]::UtcNow
                }
                else {
                    Write-Host "vastai query ambiguous; continuing polls"
                    $unknownSince = [datetime]::UtcNow
                }
            }
        }

        # Loading timeout applies only until the pidfile exists.
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
    Write-Warning "CRITICAL: Launched without -StartMonitor. Remote watchdog covers early SETUP_FAILED only."
    Write-Host "Fetch/destroy when train finishes:"
    Write-Host "  .\vast_sft_s8_weighted_orchestrate.ps1 -Go -StartMonitor"
    Write-Host "  (or re-run fetch by hand from the session SSH)"
    try { Stop-Transcript | Out-Null } catch { }
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
        "/workspace/sft_setup.log",
        "/workspace/sft_smoke.log",
        "/workspace/sft_watchdog.log",
        "/workspace/sft_fail_evidence",
        "/workspace/sft_pip_freeze.txt",
        "/workspace/sft_train.pid",
        "/workspace/sft_train.exit",
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
    Save-WeightedEvidence -Reason "post-fetch-destroy"
    & "$PSScriptRoot\vast_destroy.ps1" -Force
}

if (-not $adapterOk) {
    throw "Weighted adapter missing after fetch. Check $ResultsDir and sft_train.log before another go."
}

Write-Host "WEIGHTED SFT COMPLETE -- artifacts in $ResultsDir"
Write-Host "No Hub upload. Score RAG with sft_export_if_gates.ps1 later."
try { Stop-Transcript | Out-Null } catch { }
exit 0
