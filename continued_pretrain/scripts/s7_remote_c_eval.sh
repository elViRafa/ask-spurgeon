#!/usr/bin/env bash
# C eval for S7 Phase A. Prefers theology_cpt_lora_s5best; falls back to theology_cpt_lora.
# Stack pin matches B / isolation-C: Unsloth 2026.8.22 + torch 2.8 (no xformers).
#
# Usage:
#   bash s7_remote_c_eval.sh                         # SHA skip (loud warn)
#   EXPECTED_ADAPTER_SHA256=<hex> bash s7_remote_c_eval.sh
#   S7_EVAL_ADAPTER=/workspace/theology_cpt_lora bash s7_remote_c_eval.sh
set -euo pipefail

WORK=/workspace
S5BEST="$WORK/theology_cpt_lora_s5best"
LORA="$WORK/theology_cpt_lora"
STAGE="$WORK/theology_cpt_lora_s7_eval_stage"

export CPT_WORK_ROOT=$WORK
export CPT_DATA_ROOT=$WORK
export HF_HOME=$WORK/hf_home
export PYTHONUNBUFFERED=1
export UNSLOTH_PIP_SPEC="${UNSLOTH_PIP_SPEC:-unsloth[colab-new]==2026.8.22}"
export UNSLOTH_SKIP_TORCHVISION_CHECK="${UNSLOTH_SKIP_TORCHVISION_CHECK:-1}"

# Prefer s5best; allow explicit override.
if [[ -n "${S7_EVAL_ADAPTER:-}" ]]; then
  SRC="$S7_EVAL_ADAPTER"
elif [[ -f "$S5BEST/adapter_model.safetensors" ]]; then
  SRC="$S5BEST"
else
  SRC="$LORA"
fi

if [[ ! -f "$SRC/adapter_model.safetensors" ]]; then
  echo "FAIL: missing adapter at $SRC" >&2
  exit 1
fi

SHA=$(python3 -c "import hashlib; p='$SRC/adapter_model.safetensors'; print(hashlib.sha256(open(p,'rb').read()).hexdigest())")
echo "S7 C eval adapter: $SRC"
echo "adapter sha256: $SHA"

# Default EXPECTED to skip so eval_cpt_sota.py's S6 6aab default does not hard-fail S7.
# Pass EXPECTED_ADAPTER_SHA256=<hex> to pin.
if [[ -z "${EXPECTED_ADAPTER_SHA256:-}" ]]; then
  export EXPECTED_ADAPTER_SHA256=skip
  echo "WARNING: EXPECTED_ADAPTER_SHA256 unset — using skip (will not pin SHA)."
  echo "WARNING: set EXPECTED_ADAPTER_SHA256=$SHA to pin this adapter."
else
  export EXPECTED_ADAPTER_SHA256
  echo "EXPECTED_ADAPTER_SHA256=$EXPECTED_ADAPTER_SHA256"
fi

# Stage into theology_cpt_lora so eval_cpt_sota finds it (without mutating s5best).
if [[ "$SRC" != "$LORA" ]]; then
  rm -rf "$STAGE"
  mkdir -p "$STAGE"
  for f in adapter_model.safetensors adapter_config.json tokenizer.json tokenizer_config.json README.md s5_best.json; do
    if [[ -f "$SRC/$f" ]]; then
      cp -a "$SRC/$f" "$STAGE/"
    fi
  done
  rm -rf "$LORA"
  cp -a "$STAGE" "$LORA"
  echo "Staged $SRC -> $LORA for C eval"
fi

pin_torch_and_unsloth() {
  local py="${1:-python3}"
  echo "Pinning torch 2.8.0+cu126 + torchvision 0.23.0 + torchaudio 2.8.0"
  "$py" -m pip install -q --break-system-packages \
    torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 \
    --index-url https://download.pytorch.org/whl/cu126
  echo "Installing $UNSLOTH_PIP_SPEC (no-deps after torch pin)"
  "$py" -m pip install -q --break-system-packages --no-deps "$UNSLOTH_PIP_SPEC" || \
    "$py" -m pip install -q --break-system-packages "$UNSLOTH_PIP_SPEC"
  "$py" -m pip uninstall -y xformers 2>/dev/null || true
  "$py" - <<'PY'
import torch
print("torch", torch.__version__)
assert torch.__version__.startswith("2.8"), torch.__version__
PY
}

cd "$WORK"
if ! python3 -c "import unsloth, torch; assert torch.__version__.startswith('2.8')" 2>/dev/null; then
  echo "Installing S7 C stack pin (Unsloth 2026.8.22 / torch 2.8)..."
  pin_torch_and_unsloth python3
else
  echo "Unsloth + torch 2.8 already present"
fi

python3 -u /workspace/eval_cpt_sota.py --preflight
nohup env \
  EXPECTED_ADAPTER_SHA256="$EXPECTED_ADAPTER_SHA256" \
  UNSLOTH_PIP_SPEC="$UNSLOTH_PIP_SPEC" \
  UNSLOTH_SKIP_TORCHVISION_CHECK=1 \
  python3 -u /workspace/eval_cpt_sota.py > /workspace/cpt_eval.log 2>&1 &
echo "C eval PID $! — tail -f /workspace/cpt_eval.log"
sleep 8
tail -n 40 /workspace/cpt_eval.log
