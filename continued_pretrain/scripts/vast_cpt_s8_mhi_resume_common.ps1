# Shared Vast CPT m_hi resume defaults. Dot this only from -Go scripts.
# Dry orchestrate must not dot this file (it loads the Vast CLI helpers).
$ErrorActionPreference = "Stop"

$Script:CptRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Script:RepoRootFromCpt = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$FtScripts = Join-Path $RepoRootFromCpt "fine_tuning\scripts"

if (-not $env:VAST_SESSION_FILE -or -not $env:VAST_SESSION_FILE.Trim()) {
    $env:VAST_SESSION_FILE = Join-Path $CptRoot "kaggle\runpod_cpt_v3\vast_cpt_s8_mhi_resume_session.json"
}
if (-not $env:VAST_LOCAL_RESULTS_DIR -or -not $env:VAST_LOCAL_RESULTS_DIR.Trim()) {
    $env:VAST_LOCAL_RESULTS_DIR = Join-Path $CptRoot "kaggle\runpod_cpt_v3\vast_cpt_s8_mhi_resume"
}

. (Join-Path $FtScripts "vast_common.ps1")

$Script:DefaultDiskGb = 160
$Script:DefaultLabel = "cpt-s8-mhi-resume"
$Script:MaxWallHours = 10
$Script:SearchQuery = "num_gpus=1 gpu_name=RTX_4090 reliability>=0.90 disk_space>=140 gpu_frac>=1 cuda_max_good>=12.6"
$Script:MergeAdapterSha = "a70fded8aea1c9cb1a484e640e89137412519c28d95bdbfbf8d73ca2d2e42eac"
$Script:InitAdapterSha = "8c1db3db74bcf03b876740a5cf8884899fb3efda4945a2ae74a02655a8359b84"
$Script:MixSha = "ad817213af207428785c4cfac12ddc1bc390b3e59d6e97b43491fafdafe91962"
$Script:MixRel = "kaggle\a_output_v6_p0"
$Script:MergeLoraRel = "kaggle\runpod_cpt_v3\vast_cpt_s7_p0\fetch\theology_cpt_lora_s5best"
$Script:ResumeCkptRel = "kaggle\runpod_cpt_v3\vast_cpt_s8_mhi_continue\fetch\mhi_continue\checkpoints\checkpoint-800"

function Get-VastCptMhiMixDir {
    return (Join-Path $CptRoot $MixRel)
}

function Get-VastCptMhiMergeLoraDir {
    return (Join-Path $CptRoot $MergeLoraRel)
}

function Get-VastCptMhiResumeCkptDir {
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
}
