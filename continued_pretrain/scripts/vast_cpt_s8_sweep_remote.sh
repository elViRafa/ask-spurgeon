#!/usr/bin/env bash
# S8 plateau sweep on Vast. Merge a70fded8, then three fresh r=128 arms.
# Does nothing until the orchestrator launches it after operator go.
# Stack pin: Unsloth 2026.8.22 + torch 2.8. New Adam. No Hub.
set -euo pipefail

export CPT_DATA_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export PYTHONUNBUFFERED=1
export DEBIAN_FRONTEND=noninteractive
export GPU_PROFILE="${GPU_PROFILE:-ampere}"
export UNSLOTH_PIP_SPEC="${UNSLOTH_PIP_SPEC:-unsloth[colab-new]==2026.8.22}"
export UNSLOTH_SKIP_TORCHVISION_CHECK="${UNSLOTH_SKIP_TORCHVISION_CHECK:-1}"
PINNED_ADAPTER_SHA256="${EXPECTED_ADAPTER_SHA256:-a70fded8aea1c9cb1a484e640e89137412519c28d95bdbfbf8d73ca2d2e42eac}"
MERGED_DIR=/workspace/theology_cpt_merged_a70
PLAN=/workspace/vast_cpt_s8_sweep_plan.py

mkdir -p "$HF_HOME" /workspace/unsloth_offload /workspace/miniforge3 /workspace/sweep

if [[ -f /workspace/.sft_env ]]; then
  # shellcheck disable=SC1091
  source /workspace/.sft_env
fi
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
    echo "Installing torch 2.8.0+cu126 (isolation-C pin)"
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

if [[ ! -d /workspace/theology_dataset ]]; then
  echo "MISSING /workspace/theology_dataset — sync a_output_v6_p0 first" >&2
  exit 2
fi
if [[ ! -f /workspace/theology_cpt_lora/adapter_model.safetensors ]]; then
  echo "MISSING /workspace/theology_cpt_lora/adapter_model.safetensors (a70fded8)" >&2
  exit 2
fi
if [[ ! -f /workspace/train_cpt_sota.py || ! -f "$PLAN" || ! -f /workspace/merge_cpt_lora.py ]]; then
  echo "MISSING train, sweep plan, or merge_cpt_lora.py under /workspace" >&2
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

export SFT_WORK_ROOT=/workspace
export SFT_CPT_ADAPTER=/workspace/theology_cpt_lora
export SFT_GATE0_MERGED="$MERGED_DIR"
export EXPECTED_ADAPTER_SHA256="$PINNED_ADAPTER_SHA256"
echo "Merging a70fded8 into $MERGED_DIR (skip if config.json already exists)"
"$PY" -u /workspace/merge_cpt_lora.py
test -f "$MERGED_DIR/config.json"

train_arm() {
  local arm="$1"
  local log="$2"
  shift 2
  mkdir -p "/workspace/sweep/${arm}"
  set +e
  (
    set -euo pipefail
    unset CPT_CONTINUE_PROFILE
    emit_file="/workspace/sweep/${arm}/arm_env.sh"
    "$PY" "$PLAN" --emit-arm "$arm" "$@" >"$emit_file"
    test -s "$emit_file"
    # shellcheck disable=SC1090
    source "$emit_file"
    test -n "${CPT_RUN_MODE:-}"
    test -n "${LEARNING_RATE:-}"
    test -n "${MAX_STEPS:-}"
    exec "$PY" -u /workspace/train_cpt_sota.py
  ) >"$log" 2>&1
  local rc=$?
  set -e
  return "$rc"
}

run_arm() {
  local arm="$1"
  local log="/workspace/sweep/${arm}/cpt_train.log"
  echo "ARM_START $arm"
  set +e
  train_arm "$arm" "$log"
  local rc=$?
  set -e
  if grep -q -E "CUDA out of memory|OutOfMemoryError" "$log"; then
    echo "ARM_OOM $arm — retry LORA_RANK=64 LORA_ALPHA=45"
    log="/workspace/sweep/${arm}/cpt_train_r64.log"
    set +e
    train_arm "$arm" "$log" --oom-fallback
    rc=$?
    set -e
  fi
  echo "ARM_EXIT $arm rc=$rc"
  if [[ "$rc" -ne 0 ]]; then
    echo "arm $arm failed; see $log" >&2
    exit "$rc"
  fi
}

# Foreground arms. The orchestrator nohups this whole script.
run_arm m_lo
run_arm m_hi
run_arm f_hi
"$PY" "$PLAN" --summarize /workspace/sweep || true
echo "VAST_CPT_S8_SWEEP_DONE"
