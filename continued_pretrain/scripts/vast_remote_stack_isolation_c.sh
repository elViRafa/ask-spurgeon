#!/usr/bin/env bash
# Vast stack-isolation C: same SHA 6aab, but Hub-v2/S5 software pin (torch 2.8 + Unsloth 2026.8.22).
# Contrasts with vast_remote_c_eval.sh which installs torch 2.11 + floating unsloth.git.
set -euo pipefail

export CPT_WORK_ROOT=/workspace
export CPT_DATA_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export PYTHONUNBUFFERED=1
export DEBIAN_FRONTEND=noninteractive
PINNED_ADAPTER_SHA256="${EXPECTED_ADAPTER_SHA256:-6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c}"
export REQUIRE_AMPERE=1
export UNSLOTH_PIP_SPEC="${UNSLOTH_PIP_SPEC:-unsloth[colab-new]==2026.8.22}"
export CPT_EVAL_TRAIN_PROBE_DOCS="${CPT_EVAL_TRAIN_PROBE_DOCS:-16}"

mkdir -p "$HF_HOME" /workspace/unsloth_offload /workspace/miniforge3

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
ENV_NAME=unsloth_cpt_s5pin
PY="$CONDA_ROOT/envs/$ENV_NAME/bin/python"
LORA=/workspace/theology_cpt_lora
WEIGHTS="$LORA/adapter_model.safetensors"
LOG=/workspace/cpt_eval.log
METRICS=/workspace/theology_cpt_eval_metrics.json

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
# Exact Hub-v2/S5 major.minor: 2.8.x
assert ver[:2] == (2, 8), f"want torch 2.8.x got {torch.__version__}"
print("torch_ok", torch.__version__, torch.cuda.get_device_name(0))
PY
  if [[ "$NEED_TORCH" == "1" ]]; then
    echo "Installing torch 2.8.0+cu126 via pip into conda env (S5/Hub-v2 pin)"
    pip install -q --upgrade pip
    pip install -q torch==2.8.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
  fi

  NEED_UNSLOTH=0
  python - <<'PY' || NEED_UNSLOTH=1
import unsloth, trl, peft, datasets, transformers
print("deps_ok", getattr(unsloth, "__version__", "?"))
PY
  if [[ "$NEED_UNSLOTH" == "1" ]]; then
    echo "Installing pinned Unsloth + eval deps: unsloth[colab-new]==2026.8.22"
    pip install -q --upgrade pip
    pip install -q --no-cache-dir datasets peft "trl>=0.18.0" transformers huggingface_hub accelerate bitsandbytes
    # Quote extras; do not float latest Unsloth.
    pip install -q --no-cache-dir "unsloth[colab-new]==2026.8.22"
    # Unsloth deps often bump torch/xformers — re-pin to S5/Hub-v2 stack.
    echo "Re-pinning torch 2.8.0 + torchvision 0.23.0; drop xformers (wants torch>=2.10)"
    pip uninstall -y xformers 2>/dev/null || true
    pip install -q --force-reinstall torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu126
  fi
  export UNSLOTH_SKIP_TORCHVISION_CHECK="${UNSLOTH_SKIP_TORCHVISION_CHECK:-1}"
  # Final pin check
  python - <<'PY'
import torch, unsloth
ver = tuple(int(x) for x in torch.__version__.split("+")[0].split(".")[:2])
uv = getattr(unsloth, "__version__", "?")
print("pin_check torch", torch.__version__, "unsloth", uv)
assert ver == (2, 8), f"torch pin broken: {torch.__version__}"
print("PIN_OK")
PY
}

if [[ ! -f "$WEIGHTS" ]]; then
  echo "FAIL: missing $WEIGHTS" >&2
  exit 2
fi
if [[ ! -d /workspace/theology_holdouts/spurgeon ]]; then
  echo "FAIL: missing /workspace/theology_holdouts" >&2
  exit 2
fi
if [[ ! -f /workspace/eval_cpt_sota.py ]]; then
  echo "FAIL: missing /workspace/eval_cpt_sota.py" >&2
  exit 2
fi

GOT=$(python3 -c "import hashlib; print(hashlib.sha256(open('$WEIGHTS','rb').read()).hexdigest())" 2>/dev/null || sha256sum "$WEIGHTS" | awk '{print $1}')
echo "STACK_ISOLATION_C adapter: $LORA"
echo "EXPECTED_ADAPTER_SHA256=$EXPECTED_ADAPTER_SHA256"
echo "GOT_ADAPTER_SHA256=$GOT"
echo "UNSLOTH_PIP_SPEC=$UNSLOTH_PIP_SPEC"
echo "CPT_EVAL_TRAIN_PROBE_DOCS=$CPT_EVAL_TRAIN_PROBE_DOCS"
GOT_LC=$(echo "$GOT" | tr '[:upper:]' '[:lower:]')
WANT_LC=$(echo "$EXPECTED_ADAPTER_SHA256" | tr '[:upper:]' '[:lower:]')
if [[ "$GOT_LC" != "$WANT_LC" ]]; then
  echo "FAIL: SHA256 mismatch" >&2
  exit 3
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
PY

nvidia-smi || true
echo "CONDA_SETUP_OK - starting C-eval preflight"

cd /workspace
"$PY" -u /workspace/eval_cpt_sota.py --preflight
echo "PREFLIGHT_OK - starting full C-eval (log -> $LOG)"

set +e
"$PY" -u /workspace/eval_cpt_sota.py > "$LOG" 2>&1
rc=$?
set -e

echo "C_EVAL_EXIT=$rc"
tail -n 100 "$LOG" || true

if [[ ! -f "$METRICS" ]]; then
  echo "FAIL: metrics missing after eval rc=$rc" >&2
  exit 4
fi

if [[ $rc -ne 0 ]]; then
  echo "FAIL: eval_cpt_sota.py rc=$rc (metrics present — inspect)" >&2
  exit "$rc"
fi

echo "C_EVAL_COMPLETE metrics=$METRICS"
exit 0
