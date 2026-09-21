#!/usr/bin/env bash
# Runpod stack-isolation C: SHA 6aab on S5/Hub-v2 stack (torch 2.8 + Unsloth 2026.8.22).
# Expects /workspace/theology_cpt_lora (nested files), theology_holdouts, catechism_mcq.json, eval_cpt_sota.py.
set -euo pipefail

export CPT_WORK_ROOT=/workspace
export CPT_DATA_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export PYTHONUNBUFFERED=1
export DEBIAN_FRONTEND=noninteractive
export REQUIRE_AMPERE=1

# Pin S6 ckpt-2050 LoRA (must match nested fetch SHA).
PINNED_ADAPTER_SHA256="${EXPECTED_ADAPTER_SHA256:-6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c}"
export EXPECTED_ADAPTER_SHA256="$PINNED_ADAPTER_SHA256"

# S5 C pin recovered from runpod_cpt_v3/cpt_eval.log (Unsloth 2026.8.22 / torch 2.8.0+cu128).
export UNSLOTH_PIP_SPEC="${UNSLOTH_PIP_SPEC:-unsloth[colab-new]==2026.8.22}"
# Score first 16 Spurgeon holdout docs (train-eval protocol) alongside full 50-doc C.
export CPT_EVAL_TRAIN_PROBE_DOCS="${CPT_EVAL_TRAIN_PROBE_DOCS:-16}"

if [[ -n "${HF_TOKEN:-}" ]]; then
  export HUGGING_FACE_HUB_TOKEN="$HF_TOKEN"
fi

LORA=/workspace/theology_cpt_lora
WEIGHTS="$LORA/adapter_model.safetensors"
LOG=/workspace/cpt_eval.log
METRICS=/workspace/theology_cpt_eval_metrics.json

mkdir -p "$HF_HOME" /workspace/unsloth_offload

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

GOT=$(python3 -c "import hashlib; print(hashlib.sha256(open('$WEIGHTS','rb').read()).hexdigest())")
echo "STACK_ISOLATION_C adapter=$LORA"
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

python3 - <<'PY'
import torch
print("torch", torch.__version__, "cuda", torch.cuda.is_available(), torch.cuda.get_device_name(0))
ver = tuple(int(x) for x in torch.__version__.split("+")[0].split(".")[:2])
assert ver >= (2, 8), f"need torch>=2.8 for Hub-v2 stack, got {torch.__version__}"
PY

cd /workspace
python3 -u /workspace/eval_cpt_sota.py --preflight
echo "PREFLIGHT_OK"

# Install pinned Unsloth (does not float latest git).
python3 -u /workspace/eval_cpt_sota.py --install
echo "INSTALL_OK"

python3 - <<'PY'
import unsloth, torch
print("unsloth", getattr(unsloth, "__version__", "?"), "torch", torch.__version__)
PY

echo "Starting full C-eval (log -> $LOG)"
set +e
python3 -u /workspace/eval_cpt_sota.py > "$LOG" 2>&1
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
