#!/usr/bin/env bash
# On-pod launcher for S7 Phase B continue-B (new Adam from S7 s5best on a_output_v5).
# Opposite resume policy from s6_remote_continue_b.sh: never auto-resume
# leftover /workspace/checkpoints_sota (2050/2400).
#
# Do NOT start this until the operator says go. Prep-only until then.
set -euo pipefail

export CPT_WORK_ROOT=/workspace
export CPT_DATA_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export PYTHONUNBUFFERED=1
export CPT_RUN_MODE=continue
export CPT_CONTINUE_PROFILE=s7
export CPT_INIT_ADAPTER=/workspace/theology_cpt_lora
# Hub / local S7 s5best. Not S6 6aab and not S5 ef4df3a3.
export EXPECTED_ADAPTER_SHA256=06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432
export EVAL_DOCS_PER_BUCKET=16
export UNSLOTH_PIP_SPEC="${UNSLOTH_PIP_SPEC:-unsloth[colab-new]==2026.8.22}"
export UNSLOTH_SKIP_TORCHVISION_CHECK="${UNSLOTH_SKIP_TORCHVISION_CHECK:-1}"
# Seed composite halt from S6 in-train @ ckpt-2050 (not isolation-C full-holdout CE).
if [[ -z "${COMPOSITE_SEED_BESTS:-}" ]]; then
  # Holdout seeds only — do not seed mix-val loss on the v5 split.
  export COMPOSITE_SEED_BESTS='{"eval_spurgeon_loss":2.4987,"eval_puritan_loss":1.751,"eval_confession_loss":1.668}'
fi
export CONTINUE_MAX_STEPS="${CONTINUE_MAX_STEPS:-955}"
export EARLY_STOP_MIN_STEPS="${EARLY_STOP_MIN_STEPS:-400}"

cd /workspace
mkdir -p "$HF_HOME" /workspace/checkpoints_s7 /workspace/unsloth_offload

# Resume policy:
#   Default / first launch — PREV_RUN_CHECKPOINT= (empty string) → new Adam from S6 LoRA.
#   NEVER unset PREV when checkpoints_sota exists (that auto-picks highest sota ckpt).
#   S7_RESUME=1 — mid-S7 interrupt only: HF-resume highest complete checkpoint under checkpoints_s7.
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
  echo "PREV_RUN_CHECKPOINT empty — S7 Phase A new Adam from S6 LoRA (no HF resume)"
  if [[ -d /workspace/checkpoints_sota ]]; then
    echo "NOTE: /workspace/checkpoints_sota present but ignored (S7 never auto-resumes sota)"
  fi
fi

pin_torch_and_unsloth() {
  # Match stack-isolation C: Unsloth 2026.8.22 + torch 2.8 + torchvision 0.23.
  # Omit xformers (pulls torch>=2.10). Do not call unpinned train_cpt_sota.py --install.
  local py="${1:-python3}"
  echo "Pinning torch 2.8.0+cu126 + torchvision 0.23.0 + torchaudio 2.8.0"
  "$py" -m pip install -q --break-system-packages \
    torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 \
    --index-url https://download.pytorch.org/whl/cu126
  echo "Installing $UNSLOTH_PIP_SPEC (no-deps after torch pin)"
  "$py" -m pip install -q --break-system-packages --no-deps "$UNSLOTH_PIP_SPEC" || \
    "$py" -m pip install -q --break-system-packages "$UNSLOTH_PIP_SPEC"
  # Drop xformers if a transitive install pulled it (wants torch>=2.10).
  "$py" -m pip uninstall -y xformers 2>/dev/null || true
  "$py" - <<'PY'
import torch
print("torch", torch.__version__)
assert torch.__version__.startswith("2.8"), torch.__version__
try:
    import torchvision
    print("torchvision", torchvision.__version__)
except Exception as e:
    print("torchvision check:", e)
PY
}

if ! python3 -c "import unsloth, torch; assert torch.__version__.startswith('2.8')" 2>/dev/null; then
  echo "Installing S7 stack pin (Unsloth 2026.8.22 / torch 2.8)..."
  pin_torch_and_unsloth python3
else
  echo "Unsloth + torch 2.8 already present"
fi

if pgrep -f "train_cpt_sota.py" >/dev/null 2>&1; then
  echo "train_cpt_sota.py already running"
  exit 0
fi

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
  PREV_RUN_CHECKPOINT="${PREV_RUN_CHECKPOINT}" \
  UNSLOTH_PIP_SPEC="$UNSLOTH_PIP_SPEC" \
  UNSLOTH_SKIP_TORCHVISION_CHECK=1 \
  COMPOSITE_SEED_BESTS="$COMPOSITE_SEED_BESTS" \
  CONTINUE_MAX_STEPS="$CONTINUE_MAX_STEPS" \
  EARLY_STOP_MIN_STEPS="$EARLY_STOP_MIN_STEPS" \
  python3 -u /workspace/train_cpt_sota.py > /workspace/cpt_train.log 2>&1 &
echo "Started PID $! — tail -f /workspace/cpt_train.log"
sleep 5
tail -n 80 /workspace/cpt_train.log
