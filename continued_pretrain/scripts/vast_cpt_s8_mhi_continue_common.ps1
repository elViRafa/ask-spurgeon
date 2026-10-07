# Shared Vast CPT m_hi continue defaults. Dot this only from -Go scripts.
# Dry orchestrate must not dot this file (it loads the Vast CLI helpers).
$ErrorActionPreference = "Stop"

$Script:CptRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Script:RepoRootFromCpt = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$FtScripts = Join-Path $RepoRootFromCpt "fine_tuning\scripts"

if (-not $env:VAST_SESSION_FILE -or -not $env:VAST_SESSION_FILE.Trim()) {
    $env:VAST_SESSION_FILE = Join-Path $CptRoot "kaggle\runpod_cpt_v3\vast_cpt_s8_mhi_continue_session.json"
}
if (-not $env:VAST_LOCAL_RESULTS_DIR -or -not $env:VAST_LOCAL_RESULTS_DIR.Trim()) {
    $env:VAST_LOCAL_RESULTS_DIR = Join-Path $CptRoot "kaggle\runpod_cpt_v3\vast_cpt_s8_mhi_continue"
}

. (Join-Path $FtScripts "vast_common.ps1")

$Script:DefaultDiskGb = 150
$Script:DefaultLabel = "cpt-s8-mhi-continue"
$Script:MaxWallHours = 8
$Script:SearchQuery = "num_gpus=1 gpu_name=RTX_4090 reliability>=0.90 disk_space>=120 gpu_frac>=1 cuda_max_good>=12.6"
$Script:MergeAdapterSha = "a70fded8aea1c9cb1a484e640e89137412519c28d95bdbfbf8d73ca2d2e42eac"
$Script:InitAdapterSha = "15781d964f6ca053033b08ddf9154634493513d20c9b4699faa7936fc0fe2754"
$Script:MixSha = "ad817213af207428785c4cfac12ddc1bc390b3e59d6e97b43491fafdafe91962"
$Script:MixRel = "kaggle\a_output_v6_p0"
$Script:MergeLoraRel = "kaggle\runpod_cpt_v3\vast_cpt_s7_p0\fetch\theology_cpt_lora_s5best"
$Script:InitLoraRel = "kaggle\runpod_cpt_v3\vast_cpt_s8_sweep\fetch\sweep\m_hi\theology_cpt_lora"

function Get-VastCptMhiMixDir {
    return (Join-Path $CptRoot $MixRel)
}

function Get-VastCptMhiMergeLoraDir {
    return (Join-Path $CptRoot $MergeLoraRel)
}

function Get-VastCptMhiInitLoraDir {
    return (Join-Path $CptRoot $InitLoraRel)
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
