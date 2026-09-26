#!/usr/bin/env bash
# Vast S7 holdout-sibling continue on a_output_v6. Miniforge + isolation-C stack pin.
# Init Phase B C-winner s5best ddbbee3a with a new Adam. Do NOT HF-resume v3 / sota.
set -euo pipefail

export CPT_WORK_ROOT=/workspace
export CPT_DATA_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export PYTHONUNBUFFERED=1
export DEBIAN_FRONTEND=noninteractive
export CPT_RUN_MODE=continue
export CPT_CONTINUE_PROFILE=s7
export CPT_INIT_ADAPTER=/workspace/theology_cpt_lora
export EVAL_DOCS_PER_BUCKET=16
export GPU_PROFILE="${GPU_PROFILE:-ampere}"
export UNSLOTH_PIP_SPEC="${UNSLOTH_PIP_SPEC:-unsloth[colab-new]==2026.8.22}"
export UNSLOTH_SKIP_TORCHVISION_CHECK="${UNSLOTH_SKIP_TORCHVISION_CHECK:-1}"
# Capture before .sft_env (HF inject may overwrite EXPECTED_ADAPTER_SHA256).
PINNED_ADAPTER_SHA256="${EXPECTED_ADAPTER_SHA256:-ddbbee3ac9ef7baf6cca21dcdb844d027d39f5f6a4b88ba10fcf8a43fa7c8214}"

if [[ -z "${COMPOSITE_SEED_BESTS:-}" ]]; then
  # Holdout seeds only — do not seed mix-val loss.
  export COMPOSITE_SEED_BESTS='{"eval_spurgeon_loss":2.4987,"eval_puritan_loss":1.751,"eval_confession_loss":1.668}'
fi
if [[ -z "${COMPOSITE_EARLY_STOP_METRICS:-}" ]]; then
  export COMPOSITE_EARLY_STOP_METRICS='eval_spurgeon_loss,eval_puritan_loss,eval_confession_loss'
fi
export CONTINUE_MAX_STEPS="${CONTINUE_MAX_STEPS:-955}"
export EARLY_STOP_MIN_STEPS="${EARLY_STOP_MIN_STEPS:-400}"

mkdir -p "$HF_HOME" /workspace/unsloth_offload /workspace/miniforge3 /workspace/checkpoints_s7

if [[ -f /workspace/.sft_env ]]; then
  # shellcheck disable=SC1091
  source /workspace/.sft_env
fi
# Must follow .sft_env: re-pin Phase B C-winner SHA (ddbbee3a), not whatever inject wrote.
export EXPECTED_ADAPTER_SHA256="$PINNED_ADAPTER_SHA256"
if [[ -n "${HF_TOKEN:-}" ]]; then
  export HUGGING_FACE_HUB_TOKEN="$HF_TOKEN"
fi

unset LD_LIBRARY_PATH || true

CONDA_ROOT=/workspace/miniforge3
ENV_NAME=unsloth_cpt_s7
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
ver = tuple(int(x) for x in torch.__version__.split("+")[0].split(".")[:3])
assert torch.cuda.is_available(), "cuda required"
assert ver[:2] == (2, 8), f"want torch 2.8.x got {torch.__version__}"
print("torch_ok", torch.__version__, torch.cuda.get_device_name(0))
PY
  if [[ "$NEED_TORCH" == "1" ]]; then
    echo "Installing torch 2.8.0+cu126 via pip into conda env (S7 / isolation-C pin)"
    pip install -q --upgrade pip
    pip install -q torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 \
      --index-url https://download.pytorch.org/whl/cu126
  fi

  NEED_UNSLOTH=0
  python - <<'PY' || NEED_UNSLOTH=1
import unsloth, trl, peft, datasets, transformers
print("deps_ok", getattr(unsloth, "__version__", "?"))
PY
  if [[ "$NEED_UNSLOTH" == "1" ]]; then
    echo "Installing pinned Unsloth + train deps: $UNSLOTH_PIP_SPEC"
    pip install -q --upgrade pip
    pip install -q --no-cache-dir datasets peft "trl>=0.18.0,<0.24" transformers huggingface_hub accelerate bitsandbytes
    pip install -q --no-cache-dir "$UNSLOTH_PIP_SPEC"
    echo "Re-pinning torch 2.8.0 + torchvision 0.23.0; drop xformers (wants torch>=2.10)"
    pip uninstall -y xformers 2>/dev/null || true
    pip install -q --force-reinstall torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 \
      --index-url https://download.pytorch.org/whl/cu126
  fi
  export UNSLOTH_SKIP_TORCHVISION_CHECK=1
  python - <<'PY'
import torch, unsloth
ver = tuple(int(x) for x in torch.__version__.split("+")[0].split(".")[:2])
uv = getattr(unsloth, "__version__", "?")
print("pin_check torch", torch.__version__, "unsloth", uv)
assert ver == (2, 8), f"torch pin broken: {torch.__version__}"
print("PIN_OK")
PY
}

# Resume policy (same as s7_remote_continue_b.sh):
#   Default — PREV_RUN_CHECKPOINT= (empty string) → new Adam from S6 LoRA.
#   NEVER unset PREV (auto-resume would pick leftover checkpoints_sota).
#   S7_RESUME=1 — mid-S7 interrupt only: HF-resume highest complete under checkpoints_s7.
if [[ "${S7_RESUME:-}" == "1" ]]; then
  BEST=""
  BEST_STEP=-1
  if [[ -d /workspace/checkpoints_s7 ]]; then
    for d in /workspace/checkpoints_s7/checkpoint-*; do
      [[ -d "$d" ]] || continue
      [[ -f "$d/trainer_state.json" ]] || continue
      step="${d##*-}"
      if [[ "$step" =~ ^[0-9]+$ ]] && (( step > BEST_STEP )); then
        BEST_STEP=$step
        BEST=$d
      fi
    done
  fi
  if [[ -z "$BEST" ]]; then
    echo "S7_RESUME=1 but no complete checkpoint under /workspace/checkpoints_s7" >&2
    exit 1
  fi
  export PREV_RUN_CHECKPOINT="$BEST"
  echo "S7_RESUME=1 — HF resume from $PREV_RUN_CHECKPOINT (continue hyperparams kept)"
else
  export PREV_RUN_CHECKPOINT=
  echo "PREV_RUN_CHECKPOINT empty — S7 replay new Adam from Phase B C-winner ddbbee3a (no HF resume)"
  if [[ -d /workspace/checkpoints_sota ]]; then
    echo "NOTE: /workspace/checkpoints_sota present but ignored (S7 never auto-resumes sota)"
  fi
fi

if [[ ! -d /workspace/theology_dataset ]]; then
  echo "MISSING /workspace/theology_dataset — sync a_output_v6 first" >&2
  exit 2
fi
if [[ ! -f /workspace/theology_cpt_lora/adapter_model.safetensors ]]; then
  echo "MISSING /workspace/theology_cpt_lora/adapter_model.safetensors (flatten nested 6aab LoRA)" >&2
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
import sys, torch, unsloth
print("python", sys.version.split()[0], sys.executable)
print("torch", torch.__version__, "cuda", torch.cuda.is_available(), torch.cuda.get_device_name(0))
print("unsloth", getattr(unsloth, "__version__", "?"))
ver = tuple(int(x) for x in torch.__version__.split("+")[0].split(".")[:2])
assert ver == (2, 8), torch.__version__
assert "unsloth_cpt_s7" in sys.executable, sys.executable
PY

nvidia-smi || true
echo "CONDA_SETUP_OK - starting S7 holdout-sibling replay"

if pgrep -f "train_cpt_sota.py" >/dev/null 2>&1; then
  echo "train_cpt_sota.py already running"
  exit 0
fi

cd /workspace
nohup env \
  CPT_WORK_ROOT=/workspace \
  CPT_DATA_ROOT=/workspace \
  HF_HOME=/workspace/hf_home \
  PYTHONUNBUFFERED=1 \
  CPT_RUN_MODE=continue \
  CPT_CONTINUE_PROFILE=s7 \
  CPT_INIT_ADAPTER=/workspace/theology_cpt_lora \
  EXPECTED_ADAPTER_SHA256="$EXPECTED_ADAPTER_SHA256" \
  EVAL_DOCS_PER_BUCKET=16 \
  GPU_PROFILE="$GPU_PROFILE" \
  PREV_RUN_CHECKPOINT="${PREV_RUN_CHECKPOINT}" \
  UNSLOTH_PIP_SPEC="$UNSLOTH_PIP_SPEC" \
  UNSLOTH_SKIP_TORCHVISION_CHECK=1 \
  COMPOSITE_SEED_BESTS="$COMPOSITE_SEED_BESTS" \
  COMPOSITE_EARLY_STOP_METRICS="${COMPOSITE_EARLY_STOP_METRICS:-}" \
  CONTINUE_MAX_STEPS="$CONTINUE_MAX_STEPS" \
  EARLY_STOP_MIN_STEPS="$EARLY_STOP_MIN_STEPS" \
  "$PY" -u /workspace/train_cpt_sota.py > /workspace/cpt_train.log 2>&1 &
echo "Started PID $! — tail -f /workspace/cpt_train.log"
sleep 8
tail -n 80 /workspace/cpt_train.log || true
echo "VAST_CPT_S7_CONTINUE_B_LAUNCHED"
