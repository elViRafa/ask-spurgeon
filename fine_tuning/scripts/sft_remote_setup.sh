#!/usr/bin/env bash
# SFT GATE-0: kaggle path shim + torch 2.11 + Unsloth smoke + unzip qa mix.
set -euo pipefail
export SFT_WORK_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export PYTHONUNBUFFERED=1

if [[ -f /workspace/.sft_env ]]; then
  # shellcheck disable=SC1091
  source /workspace/.sft_env
fi

if [[ "${SFT_GPU_PROFILE:-}" == "a16" ]]; then
  export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
  export SFT_PER_DEVICE_BATCH="${SFT_PER_DEVICE_BATCH:-1}"
  export SFT_GRAD_ACCUM="${SFT_GRAD_ACCUM:-16}"
  echo "A16 profile: CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES} BATCH=${SFT_PER_DEVICE_BATCH} GRAD_ACCUM=${SFT_GRAD_ACCUM}"
elif [[ "${SFT_GPU_PROFILE:-}" == "4090" ]]; then
  export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
  export SFT_PER_DEVICE_BATCH="${SFT_PER_DEVICE_BATCH:-2}"
  export SFT_GRAD_ACCUM="${SFT_GRAD_ACCUM:-8}"
  echo "4090 profile: CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES} BATCH=${SFT_PER_DEVICE_BATCH} GRAD_ACCUM=${SFT_GRAD_ACCUM}"
fi

# nvidia/cuda Ubuntu images ship Python 3.10 and often lack unzip.
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

ensure_unzip() {
  if command -v unzip >/dev/null 2>&1; then
    return 0
  fi
  echo "Installing unzip (missing on CUDA base images)"
  export DEBIAN_FRONTEND=noninteractive
  wait_apt
  apt-get update -qq
  wait_apt
  apt-get install -y -qq unzip
}

# Prefer apt python3.11 when system python is 3.10; fail-closed after for 3.14.
ensure_python311() {
  if python3 - <<'PY'
import sys
raise SystemExit(0 if (3, 11) <= sys.version_info[:2] <= (3, 13) else 1)
PY
  then
    return 0
  fi
  echo "Bootstrapping Python 3.11 (have: $(python3 --version 2>&1))"
  export DEBIAN_FRONTEND=noninteractive
  wait_apt
  apt-get update -qq
  wait_apt
  if ! apt-get install -y -qq python3.11 python3.11-venv python3.11-dev; then
    echo "python3.11 not in default apt — trying deadsnakes"
    wait_apt
    apt-get install -y -qq software-properties-common curl ca-certificates
    wait_apt
    add-apt-repository -y ppa:deadsnakes/ppa
    wait_apt
    apt-get update -qq
    wait_apt
    apt-get install -y -qq python3.11 python3.11-venv python3.11-dev
  fi
  # Prefer /usr/local/bin over /usr/bin (image default python3 is often 3.10).
  export PATH="/usr/local/bin:${PATH}"
  ln -sfn "$(command -v python3.11)" /usr/local/bin/python3
  ln -sfn "$(command -v python3.11)" /usr/local/bin/python
  hash -r 2>/dev/null || true
  python3.11 -m ensurepip --upgrade 2>/dev/null || curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11
}
ensure_unzip
ensure_python311
export PATH="/usr/local/bin:${PATH}"
hash -r 2>/dev/null || true
# If symlink lost the race with /usr/bin/python3, force 3.11 on PATH.
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

python3 - <<'PY'
import sys
v = sys.version_info
assert v[:2] != (3, 14), "Python 3.14 is not supported (LlamaIndex/RAG/Unsloth)"
assert (3, 11) <= v[:2] <= (3, 13), f"Need Python 3.11–3.13, got {sys.version}"
print("python", sys.version.split()[0], "exe", sys.executable)
PY

mkdir -p /kaggle/input/datasets/spurgeon-qa-mix-v1 /kaggle/working/hf_home /kaggle/working/unsloth_offload /workspace/sft_nb "$HF_HOME"

if [[ -f /workspace/spurgeon-qa-mix-v1.zip ]]; then
  unzip -o /workspace/spurgeon-qa-mix-v1.zip -d /kaggle/input/datasets/spurgeon-qa-mix-v1
fi
ls -la /kaggle/input/datasets/spurgeon-qa-mix-v1

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
    print("torch missing — installing 2.11.0+cu126")
    pip_torch()
    import torch

ver = tuple(int(x) for x in torch.__version__.split("+")[0].split(".")[:2])
print("torch", torch.__version__)
if ver < (2, 11):
    print("Upgrading torch -> 2.11.0+cu126 (required by transformers / torchao ScalingType)")
    pip_torch()
PY

python3 -m pip install -q --break-system-packages datasets peft "trl>=0.18.0" transformers huggingface_hub
python3 -m pip install -q --break-system-packages "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

python3 - <<'PY'
import torch
from torch.nn.functional import ScalingType
from trl import SFTConfig, SFTTrainer
import unsloth

if not torch.cuda.is_available():
    raise SystemExit("SMOKE FAIL: CUDA not available")
major, _ = torch.cuda.get_device_capability(0)
if major < 8:
    raise SystemExit(f"SMOKE FAIL: need Ampere+ sm_80, got {torch.cuda.get_device_capability(0)}")
print(
    "SMOKE_OK",
    "torch", torch.__version__,
    "cuda", torch.cuda.get_device_name(0),
    "cap", torch.cuda.get_device_capability(0),
    "ScalingType", ScalingType,
)
print("trl", SFTConfig.__name__, SFTTrainer.__name__)
print("unsloth", getattr(unsloth, "__version__", "ok"))
PY

echo "SETUP_OK"
