#!/usr/bin/env bash
# Vast S6 continue-B launcher. Unsloth MUST run inside Miniforge (system pip SIGSEGV).
# Does not rebuild the mix. Resumes checkpoint-2050 when present.
set -euo pipefail

export CPT_WORK_ROOT=/workspace
export CPT_DATA_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export PYTHONUNBUFFERED=1
export DEBIAN_FRONTEND=noninteractive
export CPT_RUN_MODE=continue
export CPT_INIT_ADAPTER=/workspace/theology_cpt_lora
export EVAL_DOCS_PER_BUCKET=16
export GPU_PROFILE="${GPU_PROFILE:-ampere}"

mkdir -p "$HF_HOME" /workspace/unsloth_offload /workspace/miniforge3 /workspace/checkpoints_sota

if [[ -f /workspace/.sft_env ]]; then
  # shellcheck disable=SC1091
  source /workspace/.sft_env
fi
# Must follow .sft_env: SFT inject pins Hub-v2 SHA; S6 continue-B needs S5 LoRA SHA.
export EXPECTED_ADAPTER_SHA256=ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303
if [[ -n "${HF_TOKEN:-}" ]]; then
  export HUGGING_FACE_HUB_TOKEN="$HF_TOKEN"
fi

unset LD_LIBRARY_PATH || true

CONDA_ROOT=/workspace/miniforge3
ENV_NAME=unsloth_cpt
PY="$CONDA_ROOT/envs/$ENV_NAME/bin/python"

install_miniforge() {
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

# Resume policy (continue hyperparams always kept):
#   S6_FRESH_START=1     — wipe checkpoints; adapter-only from S5 LoRA (new Adam) — DO NOT use over good ckpt
#   PREV_RUN_CHECKPOINT= — explicit empty: first continue-B (new Adam; no HF resume)
#   PREV_RUN_CHECKPOINT=/workspace/checkpoints_sota/checkpoint-2050 — HF resume
#   unset (default when checkpoints_sota exists) — auto-resume highest complete checkpoint-*
if [[ "${S6_FRESH_START:-}" == "1" ]]; then
  echo "S6_FRESH_START=1 — removing checkpoints and log (operator override)"
  rm -rf /workspace/checkpoints_sota /workspace/cpt_train.log /workspace/theology_cpt_run_config.json
  mkdir -p /workspace/checkpoints_sota
  export PREV_RUN_CHECKPOINT=
elif [[ "${PREV_RUN_CHECKPOINT+x}" == "x" ]]; then
  if [[ -z "${PREV_RUN_CHECKPOINT}" ]]; then
    echo "PREV_RUN_CHECKPOINT empty — first continue-B from S5 LoRA (new Adam; no HF resume)"
  else
    echo "Explicit PREV_RUN_CHECKPOINT=${PREV_RUN_CHECKPOINT}"
  fi
elif [[ -d /workspace/checkpoints_sota/checkpoint-2050 ]]; then
  export PREV_RUN_CHECKPOINT=/workspace/checkpoints_sota/checkpoint-2050
  echo "Default Vast resume PREV_RUN_CHECKPOINT=${PREV_RUN_CHECKPOINT}"
elif [[ -d /workspace/checkpoints_sota ]]; then
  unset PREV_RUN_CHECKPOINT
  echo "PREV_RUN_CHECKPOINT unset — auto-resume highest complete checkpoint-*"
else
  export PREV_RUN_CHECKPOINT=
  echo "No checkpoints_sota — first continue-B from S5 LoRA (new Adam)"
fi

if [[ ! -d /workspace/theology_dataset ]]; then
  echo "MISSING /workspace/theology_dataset — sync the full v3 corpus first" >&2
  exit 2
fi
if [[ ! -d /workspace/theology_cpt_lora ]]; then
  echo "MISSING /workspace/theology_cpt_lora — sync S5 LoRA first" >&2
  exit 2
fi
if [[ ! -f /workspace/train_cpt_sota.py ]]; then
  echo "MISSING /workspace/train_cpt_sota.py" >&2
  exit 2
fi

install_miniforge
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
echo "CONDA_SETUP_OK - starting S6 continue-B on full corpus v3"

if pgrep -f "train_cpt_sota.py" >/dev/null 2>&1; then
  echo "train_cpt_sota.py already running"
  exit 0
fi

cd /workspace
nohup "$PY" -u /workspace/train_cpt_sota.py > /workspace/cpt_train.log 2>&1 &
echo "Started PID $! — tail -f /workspace/cpt_train.log"
sleep 8
tail -n 80 /workspace/cpt_train.log || true
echo "VAST_CPT_CONTINUE_B_LAUNCHED"
