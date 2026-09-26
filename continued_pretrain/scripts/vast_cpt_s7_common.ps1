# Shared Vast CPT S7 holdout-sibling replay defaults (v6 + Phase B C-winner).
# Do NOT dot vast_cpt_common.ps1. Never print VAST_API_KEY / HF_TOKEN.
$ErrorActionPreference = "Stop"

$Script:CptRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Script:RepoRootFromCpt = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$FtScripts = Join-Path $RepoRootFromCpt "fine_tuning\scripts"

if (-not $env:VAST_SESSION_FILE -or -not $env:VAST_SESSION_FILE.Trim()) {
    $env:VAST_SESSION_FILE = Join-Path $CptRoot "kaggle\runpod_cpt_v3\vast_cpt_s7_replay_session.json"
}
if (-not $env:VAST_LOCAL_RESULTS_DIR -or -not $env:VAST_LOCAL_RESULTS_DIR.Trim()) {
    $env:VAST_LOCAL_RESULTS_DIR = Join-Path $CptRoot "kaggle\runpod_cpt_v3\vast_cpt_s7_replay"
}

. (Join-Path $FtScripts "vast_common.ps1")

$Script:DefaultDiskGb = 120
$Script:DefaultLabel = "cpt-s7-replay"
$Script:MaxWallHours = 12
$Script:SearchQuery = "num_gpus=1 gpu_name=RTX_4090 reliability>=0.90 disk_space>=80 gpu_frac>=1 cuda_max_good>=12.6"
$Script:S6AdapterSha = "6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c"
$Script:S7PhaseASha = "06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432"
$Script:S7AdapterSha = "ddbbee3ac9ef7baf6cca21dcdb844d027d39f5f6a4b88ba10fcf8a43fa7c8214"
$Script:MixSha = "e050787e138e3d082937e35d1a87aa139f8e980403c3e5fefcc55aa90a2465fc"
$Script:MixRel = "kaggle\a_output_v6"
$Script:FrozenV4Sha = "37a3ba50aa9efb8057d9d36227ac4547f08d35a31ccd71cf3f2d20f928131c81"
$Script:FrozenV5Sha = "61e830575138935cdf6c1b029a3128e096ff4e3633e44a464b3957b9d6e78285"
# Replay init: nested Phase B §5 export (flatten to /workspace/theology_cpt_lora on sync).
# Top-level fetch/theology_cpt_lora_s5best is still Phase A 06354dfc.
$Script:S7LoraRel = "kaggle\runpod_cpt_v3\vast_cpt_s7\fetch\theology_cpt_lora_s5best\theology_cpt_lora_s5best"

function Get-VastCptS7MixDir {
    return (Join-Path $CptRoot $MixRel)
}

function Get-VastCptS7LoraDir {
    return (Join-Path $CptRoot $S7LoraRel)
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
