# Push HF_TOKEN + A16 train env to /workspace/.sft_env (never log the token).
. "$PSScriptRoot\vultr_common.ps1"

$session = Get-VultrSession
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready"
}

$hf = Get-HfToken
$hfB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($hf))
$sshTarget = Get-VultrSshRemote $session
$sshArgs = Get-VultrSshArgs $session

$remoteCmd = @"
set -euo pipefail
python3 << 'PYEOF'
import base64, pathlib, urllib.request
token = base64.b64decode('$hfB64').decode('utf-8')
path = pathlib.Path('/workspace/.sft_env')
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(
    'export HF_TOKEN=' + repr(token) + '\n'
    'export HF_HOME=/workspace/hf_home\n'
    'export PYTHONUNBUFFERED=1\n'
    'export USE_CPT_MERGE=1\n'
    'export SFT_WORK_ROOT=/workspace\n'
    'export SFT_GATE0_MERGED=/workspace/theology_cpt_v2_merged_hf\n'
    'export SFT_CPT_ADAPTER=/workspace/theology_cpt_lora_hub_v2\n'
    'export SFT_EXPORT=0\n'
    'export SFT_GPU_PROFILE=a16\n'
    'export CUDA_VISIBLE_DEVICES=0\n'
    'export SFT_PER_DEVICE_BATCH=1\n'
    'export SFT_GRAD_ACCUM=16\n'
    'export EXPECTED_ADAPTER_SHA256=319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478\n',
    encoding='utf-8',
)
path.chmod(0o600)
req = urllib.request.Request(
    'https://huggingface.co/api/whoami-v2',
    headers={'Authorization': 'Bearer ' + token},
)
with urllib.request.urlopen(req, timeout=30) as resp:
    resp.read()
print('HF_TOKEN_OK')
PYEOF
grep -q 'source /workspace/.sft_env' /root/.bashrc 2>/dev/null || echo 'source /workspace/.sft_env' >> /root/.bashrc
"@

& ssh @($sshArgs + @($sshTarget, $remoteCmd))
if ($LASTEXITCODE -ne 0) { throw "HF_TOKEN inject failed" }
Write-Host "HF_TOKEN + A16 env injected"
