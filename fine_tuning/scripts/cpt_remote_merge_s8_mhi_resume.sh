#!/usr/bin/env bash
# Two-stage 16-bit merge on a pod: a70 -> merged_a70 -> s8 m_hi resume final HF.
# Does not upload to Hugging Face. Fetch the output folder, then destroy.
# Stack pin matches isolation C: torch 2.8 + Unsloth 2026.8.22.
# Do not pip-install a floating Unsloth or torch 2.11.
set -euo pipefail

export SFT_WORK_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export PYTHONUNBUFFERED=1
export DEBIAN_FRONTEND=noninteractive

if [[ -f /workspace/.sft_env ]]; then
  # shellcheck disable=SC1091
  source /workspace/.sft_env
fi
if [[ -n "${HF_TOKEN:-}" ]]; then
  export HUGGING_FACE_HUB_TOKEN="$HF_TOKEN"
fi
unset LD_LIBRARY_PATH || true

PARENT_DIR="${CPT_MERGE_PARENT_DIR:-/workspace/merge_parent_a70}"
RESUME_DIR="${CPT_RESUME_LORA_DIR:-/workspace/theology_cpt_lora}"
INTERMEDIATE="${CPT_MERGED_A70:-/workspace/theology_cpt_merged_a70}"
OUTPUT="${CPT_S8_MERGED_HF:-/workspace/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit}"
MERGE_SCRIPT="${CPT_S8_MERGE_PY:-/workspace/merge_cpt_s8_mhi_resume.py}"
READY_PY="${CPT_S8_READY_PY:-/workspace/cpt_s8_mhi_resume_merge_readiness.py}"
CONDA_ROOT=/workspace/miniforge3
ENV_NAME=unsloth_cpt_s5pin
PY="$CONDA_ROOT/envs/$ENV_NAME/bin/python"

mkdir -p "$HF_HOME"

finish_ok() {
  echo "CPT_S8_MHI_RESUME_MERGE_DONE output=$OUTPUT"
}

if [[ -f "$OUTPUT/config.json" ]]; then
  echo "Final merged HF already exists — skip: $OUTPUT"
  finish_ok
  exit 0
fi

if [[ ! -f "$PARENT_DIR/adapter_model.safetensors" ]]; then
  echo "FAIL: missing $PARENT_DIR/adapter_model.safetensors" >&2
  exit 2
fi
if [[ ! -f "$RESUME_DIR/adapter_model.safetensors" ]]; then
  echo "FAIL: missing $RESUME_DIR/adapter_model.safetensors" >&2
  exit 2
fi
if [[ ! -f "$MERGE_SCRIPT" ]]; then
  echo "FAIL: missing $MERGE_SCRIPT" >&2
  exit 2
fi
if [[ ! -f /workspace/merge_cpt_lora.py ]]; then
  echo "FAIL: missing /workspace/merge_cpt_lora.py" >&2
  exit 2
fi
if [[ ! -f "$READY_PY" ]]; then
  echo "FAIL: missing $READY_PY" >&2
  exit 2
fi

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
    echo "Installing torch 2.8.0+cu126 via pip into conda env"
    pip install -q --upgrade pip
    pip install -q torch==2.8.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
  fi

  NEED_UNSLOTH=0
  python - <<'PY' || NEED_UNSLOTH=1
import unsloth, peft, transformers
print("deps_ok", getattr(unsloth, "__version__", "?"))
PY
  if [[ "$NEED_UNSLOTH" == "1" ]]; then
    echo "Installing pinned Unsloth: unsloth[colab-new]==2026.8.22"
    pip install -q --upgrade pip
    pip install -q --no-cache-dir peft "trl>=0.18.0" transformers huggingface_hub accelerate bitsandbytes
    pip install -q --no-cache-dir "unsloth[colab-new]==2026.8.22"
    echo "Re-pinning torch 2.8.0; drop xformers (wants torch>=2.10)"
    pip uninstall -y xformers 2>/dev/null || true
    pip install -q --force-reinstall torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu126
  fi
  export UNSLOTH_SKIP_TORCHVISION_CHECK="${UNSLOTH_SKIP_TORCHVISION_CHECK:-1}"
  python - <<'PY'
import torch, unsloth
ver = tuple(int(x) for x in torch.__version__.split("+")[0].split(".")[:2])
print("pin_check torch", torch.__version__, "unsloth", getattr(unsloth, "__version__", "?"))
assert ver == (2, 8), f"torch pin broken: {torch.__version__}"
print("PIN_OK")
PY
}

install_miniforge
ensure_env
# shellcheck disable=SC1091
source "$CONDA_ROOT/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"
unset LD_LIBRARY_PATH || true

ARGS=(--parent-adapter "$PARENT_DIR" --resume-adapter "$RESUME_DIR" --intermediate "$INTERMEDIATE" --output "$OUTPUT")
if [[ "${SFT_MERGE_DEVICE:-}" == "cpu" ]]; then
  ARGS+=(--cpu)
fi

"$PY" -u "$MERGE_SCRIPT" --preflight "${ARGS[@]}"
"$PY" -u "$MERGE_SCRIPT" "${ARGS[@]}"
finish_ok
