#!/usr/bin/env bash
# Vast Unsloth CPT smoke inside a clean Miniconda env (GitHub #668 workaround).
set -euo pipefail
export CPT_WORK_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export PYTHONUNBUFFERED=1
export DEBIAN_FRONTEND=noninteractive
mkdir -p "$HF_HOME" /workspace/unsloth_offload /workspace/miniforge3

if [[ -f /workspace/.sft_env ]]; then
  # shellcheck disable=SC1091
  source /workspace/.sft_env
fi
if [[ -n "${HF_TOKEN:-}" ]]; then
  export HUGGING_FACE_HUB_TOKEN="$HF_TOKEN"
fi

unset LD_LIBRARY_PATH || true

CONDA_ROOT=/workspace/miniforge3
ENV_NAME=unsloth_smoke
PY="$CONDA_ROOT/envs/$ENV_NAME/bin/python"

install_miniconda() {
  if [[ -x "$CONDA_ROOT/bin/conda" ]]; then
    echo "Miniforge already present"
    return 0
  fi
  echo "Installing Miniforge to $CONDA_ROOT"
  curl -fsSL https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -o /tmp/miniforge.sh
  bash /tmp/miniforge.sh -b -u -p "$CONDA_ROOT"
  rm -f /tmp/miniforge.sh
}

ensure_env() {
  # shellcheck disable=SC1091
  source "$CONDA_ROOT/etc/profile.d/conda.sh"
  conda config --set always_yes yes
  conda config --set channel_priority flexible
  if conda env list | grep -qE "^${ENV_NAME}\\s"; then
    echo "conda env $ENV_NAME exists"
  else
    echo "Creating conda env $ENV_NAME (python 3.11)"
    conda create -y -n "$ENV_NAME" python=3.11
  fi
  conda activate "$ENV_NAME"

  NEED_TORCH=0
  python - <<'PY' || NEED_TORCH=1
import torch
ver = tuple(int(x) for x in torch.__version__.split("+")[0].split(".")[:2])
assert torch.cuda.is_available(), "cuda required"
assert ver >= (2, 4)
print("torch_ok", torch.__version__, torch.cuda.get_device_name(0))
PY
  if [[ "$NEED_TORCH" == "1" ]]; then
    echo "Installing torch 2.11.0+cu126 via pip into conda env (avoid conda-forge CPU solver)"
    pip install -q --upgrade pip
    pip install -q torch==2.11.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
  fi

  NEED_UNSLOTH=0
  python - <<'PY' || NEED_UNSLOTH=1
import unsloth, trl, peft, datasets, transformers
print("deps_ok")
PY
  if [[ "$NEED_UNSLOTH" == "1" ]]; then
    echo "Installing unsloth + train deps into conda env via pip"
    pip install -q --upgrade pip
    pip install -q datasets peft "trl>=0.18.0" transformers huggingface_hub accelerate bitsandbytes
    pip install -q "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
  fi
}

install_miniconda
ensure_env
# shellcheck disable=SC1091
source "$CONDA_ROOT/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"
unset LD_LIBRARY_PATH || true

"$PY" - <<'PY'
import sys, torch
print("python", sys.version.split()[0], sys.executable)
print("torch", torch.__version__, "cuda", torch.cuda.is_available(), torch.cuda.get_device_name(0))
import unsloth
print("unsloth_ok")
PY

nvidia-smi || true
echo "CONDA_SETUP_OK - starting Unsloth CPT LoRA smoke"

set +e
"$PY" -u /workspace/smoke_vast_unsloth_cpt.py > /workspace/cpt_unsloth_smoke.log 2>&1
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
