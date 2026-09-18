# Shared Vast CPT S6 defaults. Source this instead of fine_tuning vast_common.ps1.
# Never print VAST_API_KEY / HF_TOKEN.
$ErrorActionPreference = "Stop"

$Script:CptRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Script:RepoRootFromCpt = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$FtScripts = Join-Path $RepoRootFromCpt "fine_tuning\scripts"

if (-not $env:VAST_SESSION_FILE -or -not $env:VAST_SESSION_FILE.Trim()) {
    $env:VAST_SESSION_FILE = Join-Path $CptRoot "kaggle\runpod_cpt_v3\vast_cpt_session.json"
}
if (-not $env:VAST_LOCAL_RESULTS_DIR -or -not $env:VAST_LOCAL_RESULTS_DIR.Trim()) {
    # Keep train artifacts on C: with the repo (corpus, LoRA, ckpt, payload).
    $env:VAST_LOCAL_RESULTS_DIR = Join-Path $CptRoot "kaggle\runpod_cpt_v3\vast_cpt_s6"
}

. (Join-Path $FtScripts "vast_common.ps1")

$Script:DefaultDiskGb = 120
$Script:DefaultLabel = "cpt-s6-continue-b"
$Script:MaxWallHours = 16
$Script:SearchQuery = "num_gpus=1 gpu_name=RTX_4090 reliability>=0.90 disk_space>=80 gpu_frac>=1 cuda_max_good>=12.6"
$Script:S5AdapterSha = "ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303"
$Script:MixSha = "23dd3820baa0b657cb6528e4fdf1b2d4813c3cfa7b7c982805b4a7ff34990973"
$Script:ResumeCkptRel = "kaggle\runpod_cpt_v3\s6_continue_b\checkpoints_sota\checkpoints_sota\checkpoint-2050"

function Get-VastCptResumeCkpt {
    return (Join-Path $CptRoot $ResumeCkptRel)
}

function Show-VastAccountSummary {
    Write-Host "=== Vast account (no secrets) ==="
    try {
        $user = Invoke-VastaiJson -CliArgs @("show", "user")
        $names = @($user.PSObject.Properties.Name)
        $credit = $null
        foreach ($k in @("credit", "credits", "balance", "account_credit")) {
            if ($names -contains $k) {
                $credit = $user.$k
                break
            }
        }
        Write-Host ("credit={0}  keys={1}" -f $credit, ($names -join ","))
    }
    catch {
        Write-Host ("show user failed: {0}" -f $_.Exception.Message)
    }
    try {
        $instText = Invoke-Vastai -CliArgs @("show", "instances") -RawJson
        if ($instText -match '^\s*\[\s*\]\s*$') {
            Write-Host "instances=[]"
        }
        else {
            $n = 0
            try { $n = @((Invoke-VastaiJson -CliArgs @("show", "instances"))).Count } catch { $n = -1 }
            Write-Host "instances_count=$n (destroy leftovers before a new rent)"
        }
    }
    catch {
        Write-Host ("show instances failed: {0}" -f $_.Exception.Message)
    }
}
