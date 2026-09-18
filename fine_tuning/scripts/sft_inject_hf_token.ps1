# Push HF_TOKEN to running pod (merge needs private Hub v2 LoRA).
# Writes /workspace/.sft_env and verifies via urllib (no huggingface_hub — setup runs later).
. "$PSScriptRoot\sft_runpod_common.ps1"

$session = Get-SftSession
if (-not $session -or -not $session.ssh_host) {
    throw "SSH not ready"
}

$hf = Get-HfToken
$hfB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($hf))
$port = Get-SftSshPort $session
$sshTarget = Get-SftSshRemote $session
$sshArgs = @("-i", $SshKey, "-p", "$port", "-o", "StrictHostKeyChecking=accept-new")

$remoteCmd = @"
set -euo pipefail
python3 << 'PYEOF'
import base64, pathlib, os, urllib.request
token = base64.b64decode('$hfB64').decode('utf-8')
path = pathlib.Path('/workspace/.sft_env')
path.write_text(
    'export HF_TOKEN=' + repr(token) + '\n'
    'export HF_HOME=/workspace/hf_home\n'
    'export PYTHONUNBUFFERED=1\n',
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
Write-Host "HF_TOKEN injected on pod"
