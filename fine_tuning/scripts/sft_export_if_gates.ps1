# Run F export only after every persisted post-SFT release gate passes.
param(
    [string]$MetricsPath = ""
)

. "$PSScriptRoot\sft_runpod_common.ps1"

$localMetrics = if ($MetricsPath) { $MetricsPath } else { Join-Path $LocalResultsDir "post_sft_eval.json" }
if (-not (Test-Path $localMetrics)) {
    throw "Missing $localMetrics - run sft_run_eval.ps1 and sft_fetch_results.ps1 first"
}

$data = Get-Content $localMetrics -Raw | ConvertFrom-Json
$m = if ($data.candidate) { $data.candidate.metrics } else { $data.metrics }
$semantic = if ($data.judge) { $data.judge.summary.candidate } else { $null }
$candidateArtifact = if ($data.candidate) { $data.candidate.artifact } else { $null }
$sourceAdapter = if ($data.candidate) { $data.candidate.source_adapter } else { $null }

if ($null -eq $semantic -or $null -eq $semantic.groundedness) {
    throw "Groundedness gate missing - run the paired evaluator with --judge."
}
if ($null -eq $candidateArtifact -or -not $candidateArtifact.path -or -not $candidateArtifact.sha256) {
    throw "Candidate artifact fingerprint missing from evaluation report."
}
if (-not (Test-Path $candidateArtifact.path -PathType Leaf)) {
    throw "Evaluated candidate artifact is unavailable: $($candidateArtifact.path)"
}
$candidateHash = (Get-FileHash -Algorithm SHA256 $candidateArtifact.path).Hash.ToLower()
if ($candidateHash -ne ([string]$candidateArtifact.sha256).ToLower()) {
    throw "Candidate artifact hash does not match the approved evaluation report."
}
if ($null -eq $sourceAdapter -or -not $sourceAdapter.path -or -not $sourceAdapter.sha256) {
    throw "Source adapter fingerprint missing from evaluation report."
}
if (-not (Test-Path $sourceAdapter.path -PathType Leaf)) {
    throw "Evaluated source adapter is unavailable: $($sourceAdapter.path)"
}
$adapterHash = (Get-FileHash -Algorithm SHA256 $sourceAdapter.path).Hash.ToLower()
if ($adapterHash -ne ([string]$sourceAdapter.sha256).ToLower()) {
    throw "Source adapter hash does not match the approved evaluation report."
}
if (-not (Test-Path $data.dataset.path -PathType Leaf)) {
    throw "Evaluated frozen dataset is unavailable: $($data.dataset.path)"
}
$datasetHash = (Get-FileHash -Algorithm SHA256 $data.dataset.path).Hash.ToLower()
if ($datasetHash -ne ([string]$data.dataset.sha256).ToLower()) {
    throw "Frozen dataset hash does not match the approved evaluation report."
}

$checks = [ordered]@{
    refusal_accuracy = ([double]$m.refusal_accuracy -ge 0.85)
    echo_rate = ([double]$m.echo_rate -le 0.02)
    corrupt_rate = ([double]$m.corrupt_rate -eq 0)
    im_end_stop_rate = ([double]$m.stop_token.im_end_stop_rate -ge 0.85)
    leaked_turn_rate = ([double]$m.stop_token.leaked_turn_rate -le 0.02)
    groundedness = ([double]$semantic.groundedness -ge 4.0)
    judge_model_consistent = ([bool]$data.judge.summary.judge_model_consistent)
}
$checks.GetEnumerator() | ForEach-Object { Write-Host "$($_.Key)=$($_.Value)" }
$failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value } | ForEach-Object { $_.Key })
if ($failed.Count -gt 0) {
    throw "Release gates FAIL: $($failed -join ', '). Export override is intentionally disabled."
}
Write-Host "All persisted release gates PASS."

& "$PSScriptRoot\sft_run_eval.ps1" -Export
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& "$PSScriptRoot\sft_fetch_results.ps1"
Write-Host "Export merged HF fetched. Next: GGUF convert, upload_sft_gguf_to_hf.py, smoke_test_ollama.py"
