#!/usr/bin/env bash
# Install torch/Unsloth and run CPT Unsloth+LoRA smoke on Vast.
set -euo pipefail
export CPT_WORK_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export PYTHONUNBUFFERED=1
export DEBIAN_FRONTEND=noninteractive
mkdir -p "$HF_HOME" /workspace/unsloth_offload
# Injected by vast_inject_hf_token.ps1 (do not echo).
if [[ -f /workspace/.sft_env ]]; then
  # shellcheck disable=SC1091
  source /workspace/.sft_env
fi
if [[ -n "${HF_TOKEN:-}" ]]; then
  export HUGGING_FACE_HUB_TOKEN="$HF_TOKEN"
fi
# System CUDA on nvidia/cuda images can shadow torch's bundled libs (Unsloth PR #6905).
unset LD_LIBRARY_PATH || true
echo "LD_LIBRARY_PATH unset for torch-bundled CUDA"

wait_apt() {
  local i=0
  while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 \
     || fuser /var/lib/apt/lists/lock >/dev/null 2>&1 \
     || fuser /var/lib/dpkg/lock >/dev/null 2>&1; do
    i=$((i + 1))
    if [[ $i -gt 120 ]]; then
      echo "apt lock still held after ~10m"
      return 1
    fi
    sleep 5
  done
}

ensure_python311() {
  if python3 - <<'PY'
import sys
raise SystemExit(0 if (3, 11) <= sys.version_info[:2] <= (3, 13) else 1)
PY
  then
    return 0
  fi
  echo "Bootstrapping Python 3.11 (have: $(python3 --version 2>&1))"
  wait_apt
  apt-get update -qq
  wait_apt
  if ! apt-get install -y -qq python3.11 python3.11-venv python3.11-dev; then
    echo "python3.11 not in default apt - trying deadsnakes"
    wait_apt
    apt-get install -y -qq software-properties-common curl ca-certificates
    wait_apt
    add-apt-repository -y ppa:deadsnakes/ppa
    wait_apt
    apt-get update -qq
    wait_apt
    apt-get install -y -qq python3.11 python3.11-venv python3.11-dev
  fi
  export PATH="/usr/local/bin:${PATH}"
  ln -sfn "$(command -v python3.11)" /usr/local/bin/python3
  ln -sfn "$(command -v python3.11)" /usr/local/bin/python
  hash -r 2>/dev/null || true
  python3.11 -m ensurepip --upgrade 2>/dev/null || curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11
}

ensure_python311
export PATH="/usr/local/bin:${PATH}"
hash -r 2>/dev/null || true

if ! python3 - <<'PY'
import sys
raise SystemExit(0 if (3, 11) <= sys.version_info[:2] <= (3, 13) else 1)
PY
then
  if command -v python3.11 >/dev/null 2>&1; then
    ln -sfn "$(command -v python3.11)" /usr/local/bin/python3
    ln -sfn "$(command -v python3.11)" /usr/local/bin/python
    hash -r 2>/dev/null || true
  fi
fi

# Ensure pip even when image already had a 3.11 rc without pip.
if ! python3 -m pip --version >/dev/null 2>&1; then
  echo "pip missing - bootstrapping"
  python3 -m ensurepip --upgrade 2>/dev/null || curl -sS https://bootstrap.pypa.io/get-pip.py | python3
fi

python3 - <<'PY'
import sys
v = sys.version_info
assert (3, 11) <= v[:2] <= (3, 13), f"Need Python 3.11-3.13, got {sys.version}"
print("python", sys.version.split()[0], sys.executable)
PY

python3 -m pip install -q --upgrade pip --break-system-packages || python3 -m pip install -q --upgrade pip

python3 - <<'PY'
import subprocess, sys

def pip_torch():
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "--break-system-packages",
        "torch==2.11.0", "torchvision", "torchaudio",
        "--index-url", "https://download.pytorch.org/whl/cu126",
    ])

try:
    import torch
except ImportError:
    print("torch missing - installing 2.11.0+cu126")
    pip_torch()
    import torch

ver = tuple(int(x) for x in torch.__version__.split("+")[0].split(".")[:2])
print("torch", torch.__version__)
if ver < (2, 11):
    print("Upgrading torch -> 2.11.0+cu126")
    pip_torch()
PY

python3 -m pip install -q --break-system-packages datasets peft "trl>=0.18.0" transformers huggingface_hub accelerate
python3 -m pip install -q --break-system-packages "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

nvidia-smi || true
echo "SETUP_OK - starting Unsloth CPT LoRA smoke"

set +e
python3 -u /workspace/smoke_vast_unsloth_cpt.py > /workspace/cpt_unsloth_smoke.log 2>&1
rc=$?
set -e
tail -n 80 /workspace/cpt_unsloth_smoke.log || true
if [[ $rc -eq 139 ]]; then
  echo "CPT_UNSLOTH_SMOKE_FAIL sigsegv_exit_139"
  exit 139
fi
if grep -q "CPT_UNSLOTH_SMOKE_PASS" /workspace/cpt_unsloth_smoke.log; then
  echo "REMOTE_SMOKE_PASS"
  exit 0
fi
echo "REMOTE_SMOKE_FAIL rc=$rc"
exit "$rc"
