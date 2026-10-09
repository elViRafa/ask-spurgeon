# Shared Vast CPT S8 sweep defaults. Dot this only from -Go scripts.
# Dry orchestrate must not dot this file (it loads the Vast CLI helpers).
$ErrorActionPreference = "Stop"

$Script:CptRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Script:RepoRootFromCpt = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$FtScripts = Join-Path $RepoRootFromCpt "fine_tuning\scripts"

if (-not $env:VAST_SESSION_FILE -or -not $env:VAST_SESSION_FILE.Trim()) {
    $env:VAST_SESSION_FILE = Join-Path $CptRoot "kaggle\runpod_cpt_v3\vast_cpt_s8_sweep_session.json"
}
if (-not $env:VAST_LOCAL_RESULTS_DIR -or -not $env:VAST_LOCAL_RESULTS_DIR.Trim()) {
    $env:VAST_LOCAL_RESULTS_DIR = Join-Path $CptRoot "kaggle\runpod_cpt_v3\vast_cpt_s8_sweep"
}

. (Join-Path $FtScripts "vast_common.ps1")

$Script:DefaultDiskGb = 150
$Script:DefaultLabel = "cpt-s8-sweep"
$Script:MaxWallHours = 8
$Script:SearchQuery = "num_gpus=1 gpu_name=RTX_4090 reliability>=0.90 disk_space>=120 gpu_frac>=1 cuda_max_good>=12.6"
$Script:S8AdapterSha = "a70fded8aea1c9cb1a484e640e89137412519c28d95bdbfbf8d73ca2d2e42eac"
$Script:MixSha = "ad817213af207428785c4cfac12ddc1bc390b3e59d6e97b43491fafdafe91962"
$Script:MixRel = "kaggle\a_output_v6_p0"
$Script:S8LoraRel = "kaggle\runpod_cpt_v3\vast_cpt_s7_p0\fetch\theology_cpt_lora_s5best"

function Get-VastCptS8MixDir {
    return (Join-Path $CptRoot $MixRel)
}

function Get-VastCptS8LoraDir {
    return (Join-Path $CptRoot $S8LoraRel)
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
