#!/usr/bin/env bash
# S8 m_hi continue on Vast. Merge a70fded8, then one continue from m_hi_lora.
# Does nothing until the orchestrator launches it after operator go.
# Stack pin: Unsloth 2026.8.22 + torch 2.8. New Adam. Flat LR at the cosine floor. No Hub.
set -euo pipefail

export CPT_DATA_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export PYTHONUNBUFFERED=1
export DEBIAN_FRONTEND=noninteractive
export GPU_PROFILE="${GPU_PROFILE:-ampere}"
export UNSLOTH_PIP_SPEC="${UNSLOTH_PIP_SPEC:-unsloth[colab-new]==2026.8.22}"
export UNSLOTH_SKIP_TORCHVISION_CHECK="${UNSLOTH_SKIP_TORCHVISION_CHECK:-1}"
MERGE_SHA="${MERGE_ADAPTER_SHA256:-a70fded8aea1c9cb1a484e640e89137412519c28d95bdbfbf8d73ca2d2e42eac}"
INIT_SHA="${INIT_ADAPTER_SHA256:-15781d964f6ca053033b08ddf9154634493513d20c9b4699faa7936fc0fe2754}"
MERGED_DIR=/workspace/theology_cpt_merged_a70
PLAN=/workspace/vast_cpt_s8_mhi_continue_plan.py
WORK=/workspace/mhi_continue

# A leaked a70 pin must not reach train_cpt_sota.py. Merge sets it for one command.
unset EXPECTED_ADAPTER_SHA256 || true

mkdir -p "$HF_HOME" /workspace/unsloth_offload /workspace/miniforge3 "$WORK"

if [[ -f /workspace/.sft_env ]]; then
  # shellcheck disable=SC1091
  source /workspace/.sft_env
fi
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
if [[ ! -f /workspace/m_hi_lora/adapter_model.safetensors ]]; then
  echo "MISSING /workspace/m_hi_lora/adapter_model.safetensors" >&2
  exit 2
fi
if [[ ! -f /workspace/train_cpt_sota.py || ! -f "$PLAN" || ! -f /workspace/merge_cpt_lora.py ]]; then
  echo "MISSING train, continue plan, or merge_cpt_lora.py under /workspace" >&2
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
echo "Merging a70fded8 into $MERGED_DIR (skip if config.json already exists)"
EXPECTED_ADAPTER_SHA256="$MERGE_SHA" "$PY" -u /workspace/merge_cpt_lora.py
test -f "$MERGED_DIR/config.json"

mkdir -p "$WORK"
log="$WORK/cpt_train.log"
echo "ARM_START m_hi_continue"
set +e
(
  set -euo pipefail
  emit_file="$WORK/arm_env.sh"
  "$PY" "$PLAN" --emit >"$emit_file"
  test -s "$emit_file"
  # shellcheck disable=SC1090
  source "$emit_file"
  test "$CPT_RUN_MODE" = continue
  test "$LEARNING_RATE" = 5e-6
  test "$EMBEDDING_LEARNING_RATE" = 5e-7
  test "$MAX_STEPS" = 800
  test "$EARLY_STOP_MIN_STEPS" = 800
  test "$LR_SCHEDULER" = constant
  test "$CPT_INIT_ADAPTER" = /workspace/m_hi_lora
  echo "RECIPE_OK continue lr=$LEARNING_RATE steps=$MAX_STEPS scheduler=$LR_SCHEDULER"
  exec "$PY" -u /workspace/train_cpt_sota.py
) >"$log" 2>&1
rc=$?
set -e
echo "ARM_EXIT m_hi_continue rc=$rc"
if [[ "$rc" -ne 0 ]]; then
  echo "m_hi continue failed; see $log" >&2
  exit "$rc"
fi
echo "VAST_CPT_S8_MHI_CONTINUE_DONE"
