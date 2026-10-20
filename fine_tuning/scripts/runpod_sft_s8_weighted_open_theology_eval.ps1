# RunPod open-theology held-out score for local weighted S8 SFT LoRA.
# Default: dry readiness only (no rent). -Go provisions, merges (or reuses staging),
# generate-only on 40 OT rows, fetches, judges locally with Gemini.
# Never Hub/Ollama promote. Does not unlock export.
param(
    [switch]$Go,
    [switch]$KeepPod,
    [switch]$SmokeLimit,
    [ValidateSet("COMMUNITY", "SECURE")]
    [string]$CloudType = "SECURE",
    [double]$QuoteUsdPerHour = 0.89,
    [double]$MaxWallHours = 1.5
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$FtRoot = Join-Path $RepoRoot "fine_tuning"
$SessionFile = Join-Path $FtRoot "kaggle\runpod_sft_s8_weighted_ot_eval_session.json"
$ResultsDir = Join-Path $FtRoot "kaggle\runpod_sft_s8_weighted"
$EvalResults = Join-Path $FtRoot "eval_results"
$LocalLora = Join-Path $ResultsDir "sft_s8_weighted\adapter\lora"
$AdapterWeights = Join-Path $LocalLora "adapter_model.safetensors"
$OtEvalLocal = Join-Path $FtRoot "data\qa_open_theology\sft\open_theology_eval.jsonl"
$OtAcceptedLocal = Join-Path $FtRoot "data\qa_open_theology\eval_accepted.jsonl"
$ExpectedSha = "e891731c9a71cb78c41f3cf8e1b7bbab54ea84c2ee4371d9105d773ae616f9dd"
$Label = "sft-s8w-ot-eval"
$SshKey = Join-Path $env:USERPROFILE ".ssh\runpod_cpt"

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
New-Item -ItemType Directory -Force -Path $EvalResults | Out-Null
$TranscriptPath = Join-Path $ResultsDir ("ot_eval_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log")
try {
    Start-Transcript -Path $TranscriptPath -Append | Out-Null
    Write-Host "TRANSCRIPT=$TranscriptPath"
}
catch {
    Write-Warning ("Start-Transcript failed: {0}" -f $_.Exception.Message)
}

Write-Host "=== RunPod open-theology eval - weighted S8 SFT LoRA ==="
Write-Host "go=$Go smoke_limit=$SmokeLimit keep_pod=$KeepPod cloud=$CloudType"
Write-Host "lora=$LocalLora"
Write-Host "session=$SessionFile"
$quote = [math]::Round($QuoteUsdPerHour * $MaxWallHours, 2)
Write-Host ('cost_quote ~{0} USD for {1} hours at {2}/hr (confirm live Secure 4090 before -Go)' -f $quote, $MaxWallHours, $QuoteUsdPerHour)
Write-Host "FAIL_CLOSED: no Hub LoRA overwrite, no spurgeon-qa-v2 GGUF/Ollama, release_gate=false"

if (-not (Test-Path -LiteralPath $AdapterWeights)) {
    throw "Missing adapter weights: $AdapterWeights"
}
if (-not (Test-Path -LiteralPath $OtEvalLocal)) {
    throw "Missing OT eval set: $OtEvalLocal"
}
if (-not (Test-Path -LiteralPath $OtAcceptedLocal)) {
    throw "Missing OT accepted meta: $OtAcceptedLocal"
}

$py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

& $py -m pytest (Join-Path $PSScriptRoot "test_evaluate_open_theology.py") -q --tb=line
if ($LASTEXITCODE -ne 0) { throw "test_evaluate_open_theology failed" }

$adapterSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $AdapterWeights).Hash.ToLower()
Write-Host "ADAPTER_SHA256=$adapterSha"
if ($adapterSha -ne $ExpectedSha) {
    Write-Warning ("Adapter SHA differs from plan expected {0}" -f $ExpectedSha)
}
Write-Host "ADAPTER_BYTES=$((Get-Item -LiteralPath $AdapterWeights).Length)"
$evalLines = @(Get-Content -LiteralPath $OtEvalLocal | Where-Object { $_.Trim() }).Count
Write-Host "OT_EVAL_ROWS=$evalLines"
if ($evalLines -ne 40 -and -not $SmokeLimit) {
    Write-Warning "Expected 40 OT eval rows"
}

if (-not $Go) {
    Write-Host ""
    Write-Host "DRY COMPLETE -- no pod rented."
    Write-Host "Confirm live Secure 4090 USD/hr, then after operator go:"
    Write-Host "  `$env:SFT_EVAL_JUDGE_PROVIDER = 'gemini'"
    Write-Host "  .\fine_tuning\scripts\runpod_sft_s8_weighted_open_theology_eval.ps1 -Go"
    Write-Host "  runpodctl pod list   # verify destroy / no orphans"
    Write-Host "READY"
    try { Stop-Transcript | Out-Null } catch { }
    exit 0
}

# --- -Go only below ---
if (-not $env:SFT_EVAL_JUDGE_PROVIDER) {
    $env:SFT_EVAL_JUDGE_PROVIDER = "gemini"
}
Write-Host "SFT_EVAL_JUDGE_PROVIDER=$($env:SFT_EVAL_JUDGE_PROVIDER)"

$env:SFT_SESSION_FILE = $SessionFile
$env:SFT_LOCAL_RESULTS_DIR = $ResultsDir
. "$PSScriptRoot\sft_runpod_common.ps1"
$Script:StateFile = $SessionFile
$Script:LocalResultsDir = $ResultsDir

function Get-OtSshArgs {
    param($Session)
    $port = Get-SftSshPort $Session
    return @(
        "-T", "-i", $SshKey, "-p", "$port",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "LogLevel=ERROR",
        "-o", "ConnectTimeout=20",
        "-o", "RequestTTY=no"
    )
}

function Invoke-OtSsh([string]$Remote) {
    $session = Get-SftSession
    if (-not $session -or -not $session.ssh_host) { throw "SSH not ready" }
    $clean = $Remote -replace "`r", ""
    $last = -1
    for ($attempt = 1; $attempt -le 5; $attempt++) {
        $prev = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            $sshArgs = (Get-OtSshArgs $session) + @(
                "-o", "ServerAliveInterval=30",
                "-o", "ServerAliveCountMax=6",
                (Get-SftSshRemote $session), $clean
            )
            & ssh @sshArgs
            $last = [int]$LASTEXITCODE
        }
        finally { $ErrorActionPreference = $prev }
        if ($last -eq 0) { return }
        Write-Warning ("ssh attempt {0}/5 exit={1}" -f $attempt, $last)
        Start-Sleep -Seconds (5 * $attempt)
    }
    throw "ssh failed exit=$last"
}

function Copy-ToOtPod {
    param([string]$Local, [string]$Remote)
    $session = Get-SftSession
    $port = Get-SftSshPort $session
    $remoteHost = Get-SftSshRemote $session
    $remoteDir = (Split-Path $Remote -Parent) -replace "\\", "/"
    if ($remoteDir -and $remoteDir -ne "/" -and $remoteDir -ne ".") {
        Invoke-OtSsh "mkdir -p '$remoteDir'"
    }
    $last = -1
    for ($attempt = 1; $attempt -le 5; $attempt++) {
        $scpArgs = @(
            "-i", $SshKey, "-P", "$port",
            "-o", "StrictHostKeyChecking=accept-new", "-o", "LogLevel=ERROR",
            "-o", "ConnectTimeout=30",
            "-o", "ServerAliveInterval=30",
            $Local, "${remoteHost}:${Remote}"
        )
        $prev = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            & scp @scpArgs
            $last = [int]$LASTEXITCODE
        }
        finally { $ErrorActionPreference = $prev }
        if ($last -eq 0) { return }
        Write-Warning ("scp attempt {0}/5 exit={1}: {2}" -f $attempt, $last, $Local)
        Start-Sleep -Seconds (5 * $attempt)
    }
    throw "scp failed: $Local -> $Remote"
}

function Copy-FromOtPod {
    param([string]$Remote, [string]$Local)
    $session = Get-SftSession
    $port = Get-SftSshPort $session
    $remoteHost = Get-SftSshRemote $session
    $dir = Split-Path $Local -Parent
    if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $scpArgs = @(
        "-i", $SshKey, "-P", "$port",
        "-o", "StrictHostKeyChecking=accept-new", "-o", "LogLevel=ERROR",
        "${remoteHost}:${Remote}", $Local
    )
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & scp @scpArgs
        $sx = [int]$LASTEXITCODE
    }
    finally { $ErrorActionPreference = $prev }
    if ($sx -ne 0) { throw "scp fetch failed: $Remote -> $Local" }
}

function Invoke-DestroyOtPod {
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
        if (Test-Path $Runpodctl) { & $Runpodctl pod delete $podId 2>&1 | Out-Null }
    }
    Write-Host "Cross-check orphans with: runpodctl pod list"
}

Write-Host "Provisioning pod ($CloudType) ..."
try {
$sshReady = $false
for ($provAttempt = 1; $provAttempt -le 4; $provAttempt++) {
    Write-Host ("PROVISION_ATTEMPT={0}/4" -f $provAttempt)
    & "$PSScriptRoot\sft_provision_pod.ps1" -CloudType $CloudType -PodName $Label -SkipGate0Artifacts
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "provision failed; retrying"
        Start-Sleep -Seconds 15
        continue
    }
    Write-Host "Waiting for SSH ..."
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & "$PSScriptRoot\sft_wait_ssh.ps1" -TimeoutMinutes 12
        $waitRc = [int]$LASTEXITCODE
    }
    catch {
        $waitRc = 1
        Write-Warning $_.Exception.Message
    }
    finally { $ErrorActionPreference = $prevEap }
    if ($waitRc -eq 0) {
        $sshReady = $true
        break
    }
    Write-Warning "Bad GPU host or SSH timeout - destroy and retry"
    Invoke-DestroyOtPod -Reason "bad_host_retry"
    Start-Sleep -Seconds 20
}
if (-not $sshReady) { throw "ssh wait failed after provision retries" }

$dotenvLocal = Join-Path $env:TEMP ("sft_ot_eval_env_" + [guid]::NewGuid().ToString("N") + ".env")
try {
    $lines = @()
    $srcEnv = Join-Path $RepoRoot ".env"
    $want = @(
        "HF_TOKEN", "HUGGING_FACE_HUB_TOKEN",
        "SFT_EVAL_JUDGE_PROVIDER", "SFT_EVAL_JUDGE_API_KEY", "SFT_EVAL_JUDGE_BASE_URL", "SFT_EVAL_JUDGE_MODEL",
        "GEMINI_API_KEY", "GOOGLE_API_KEY"
    )
    if (Test-Path $srcEnv) {
        foreach ($line in Get-Content $srcEnv) {
            $t = $line.Trim()
            if (-not $t -or $t.StartsWith("#")) { continue }
            foreach ($k in $want) {
                if ($t.StartsWith("$k=")) { $lines += $t; break }
            }
        }
    }
    foreach ($k in $want) {
        $ev = [Environment]::GetEnvironmentVariable($k)
        if ($ev) { $lines += "$k=$ev" }
    }
    $lines += "HF_HOME=/workspace/hf_home"
    $map = [ordered]@{}
    foreach ($l in $lines) {
        $eq = $l.IndexOf("=")
        if ($eq -lt 1) { continue }
        $name = $l.Substring(0, $eq)
        $map[$name] = $l
    }
    if (-not $map.Contains("SFT_EVAL_JUDGE_PROVIDER")) {
        $map["SFT_EVAL_JUDGE_PROVIDER"] = "SFT_EVAL_JUDGE_PROVIDER=gemini"
    }
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    $body = (($map.Values) -join "`n") + "`n"
    [System.IO.File]::WriteAllText($dotenvLocal, $body, $utf8NoBom)
    Copy-ToOtPod -Local $dotenvLocal -Remote "/workspace/ask-spurgeon-eval/.env"
}
finally {
    if (Test-Path $dotenvLocal) { Remove-Item -Force $dotenvLocal -ErrorAction SilentlyContinue }
}

Write-Host "Uploading eval tree + LoRA + OT eval set ..."
Invoke-OtSsh @"
set -euo pipefail
mkdir -p /workspace/ask-spurgeon-eval/fine_tuning/scripts \
  /workspace/sft_s8_weighted/adapter/lora \
  /workspace/hf_home
"@

$scriptFiles = @(
    "evaluate.py", "sft_eval_core.py", "sft_stop_token_utils.py",
    "build_qa_mix.py", "qa_rewrite_checks.py",
    "merge_sft_lora.py", "sft_write_env_sh.py",
    "sft_remote_open_theology_eval_s8_weighted.sh",
    "evaluate_open_theology.py", "open_theology_qa_checks.py"
)
foreach ($name in $scriptFiles) {
    Copy-ToOtPod -Local (Join-Path $PSScriptRoot $name) `
        -Remote "/workspace/ask-spurgeon-eval/fine_tuning/scripts/$name"
}
Copy-ToOtPod -Local (Join-Path $RepoRoot "config.py") -Remote "/workspace/ask-spurgeon-eval/config.py"
Copy-ToOtPod -Local $OtEvalLocal -Remote "/workspace/open_theology_eval.jsonl"

Get-ChildItem -LiteralPath $LocalLora -File | ForEach-Object {
    Copy-ToOtPod -Local $_.FullName -Remote ("/workspace/sft_s8_weighted/adapter/lora/" + $_.Name)
}

Invoke-OtSsh @"
set -euo pipefail
chmod +x /workspace/ask-spurgeon-eval/fine_tuning/scripts/sft_remote_open_theology_eval_s8_weighted.sh
python3 /workspace/ask-spurgeon-eval/fine_tuning/scripts/sft_write_env_sh.py /workspace/ask-spurgeon-eval/.env /workspace/ask-spurgeon-eval/.env.sh
set -a
source /workspace/ask-spurgeon-eval/.env.sh
set +a
export HF_TOKEN="`${HF_TOKEN:-`$HUGGING_FACE_HUB_TOKEN}"
test -n "`$HF_TOKEN"
test -f /workspace/sft_s8_weighted/adapter/lora/adapter_model.safetensors
test -f /workspace/open_theology_eval.jsonl
echo SYNC_OK
"@

$limitEnv = if ($SmokeLimit) { "export SFT_EVAL_LIMIT=3" } else { "export SFT_EVAL_LIMIT=0" }
Write-Host "Running remote OT generate (merge reuse if present; no remote judge) ..."
$session = Get-SftSession
$cleanRemote = @"
set -euo pipefail
python3 /workspace/ask-spurgeon-eval/fine_tuning/scripts/sft_write_env_sh.py /workspace/ask-spurgeon-eval/.env /workspace/ask-spurgeon-eval/.env.sh
set -a
source /workspace/ask-spurgeon-eval/.env.sh
set +a
export HF_TOKEN="`${HF_TOKEN:-`$HUGGING_FACE_HUB_TOKEN}"
export SFT_WORK_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export SFT_LORA_DIR=/workspace/sft_s8_weighted/adapter/lora
export SFT_GATE0_MERGED=/workspace/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit
export SFT_MERGED_OUT=/workspace/spurgeon_qa_s8w_merged_hf
export SFT_EVAL_ROOT=/workspace/ask-spurgeon-eval
export SFT_OT_EVAL_SET=/workspace/open_theology_eval.jsonl
export SFT_OT_GEN_REPORT=/workspace/open_theology_eval_s8_weighted.gen.json
$limitEnv
bash /workspace/ask-spurgeon-eval/fine_tuning/scripts/sft_remote_open_theology_eval_s8_weighted.sh
"@ -replace "`r", ""
$prev = $ErrorActionPreference
$ErrorActionPreference = "Continue"
try {
    $sshArgs = (Get-OtSshArgs $session) + @(
        "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=120",
        (Get-SftSshRemote $session), $cleanRemote
    )
    & ssh @sshArgs
    $remoteEvalRc = [int]$LASTEXITCODE
}
finally { $ErrorActionPreference = $prev }
if ($remoteEvalRc -ne 0) {
    Write-Warning ("Remote OT gen exited non-zero: exit=$remoteEvalRc (will still try fetch)")
}

Write-Host "Fetching generation report ..."
$localGen = Join-Path $EvalResults "open_theology_eval_s8_weighted.gen.json"
try {
    Copy-FromOtPod -Remote "/workspace/open_theology_eval_s8_weighted.gen.json" -Local $localGen
}
catch {
    Invoke-DestroyOtPod -Reason "fetch_gen_failed"
    throw
}

Write-Host "Local OT mechanical + Gemini judge ..."
$localReport = Join-Path $EvalResults "open_theology_eval_s8_weighted.json"
& $py (Join-Path $PSScriptRoot "evaluate_open_theology.py") `
    --from-report $localGen `
    --accepted $OtAcceptedLocal `
    --eval-set $OtEvalLocal `
    --adapter-sha $adapterSha `
    --judge `
    --output $localReport
if ($LASTEXITCODE -ne 0) {
    Invoke-DestroyOtPod -Reason "local_ot_score_failed"
    throw "evaluate_open_theology.py failed"
}

Invoke-DestroyOtPod -Reason "ot_eval_complete"
Write-Host "OT_EVAL_COMPLETE report=$localReport"
Write-Host "Verify no orphans: runpodctl pod list"
try { Stop-Transcript | Out-Null } catch { }
exit 0
}
catch {
    Write-Warning ("OT_EVAL_ABORT: {0}" -f $_.Exception.Message)
    try { Invoke-DestroyOtPod -Reason "abort" } catch { Write-Warning $_.Exception.Message }
    try { Stop-Transcript | Out-Null } catch { }
    throw
}
