#!/usr/bin/env bash
# On-pod launcher for S6 continue-B. Copied to /workspace/s6_remote_continue_b.sh
set -euo pipefail

export CPT_WORK_ROOT=/workspace
export CPT_DATA_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export PYTHONUNBUFFERED=1
export CPT_RUN_MODE=continue
export CPT_INIT_ADAPTER=/workspace/theology_cpt_lora
export EXPECTED_ADAPTER_SHA256=ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303
export EVAL_DOCS_PER_BUCKET=16

# Resume policy (continue hyperparams always kept):
#   S6_FRESH_START=1     — wipe volume checkpoints; adapter-only from S5 LoRA (new Adam)
#   PREV_RUN_CHECKPOINT= — explicit empty: same as first continue-B (new Adam; no HF resume)
#   PREV_RUN_CHECKPOINT=/workspace/checkpoints_sota/checkpoint-2100 — HF resume that ckpt
#   unset (default when checkpoints_sota exists) — auto-resume highest complete checkpoint-*
#
# Do NOT point CPT_INIT_ADAPTER at checkpoint-2100 (adapter-only restart throws away Adam).
if [[ "${S6_FRESH_START:-}" == "1" ]]; then
  echo "S6_FRESH_START=1 — removing partial checkpoints and log on volume"
  rm -rf /workspace/checkpoints_sota /workspace/cpt_train.log /workspace/theology_cpt_run_config.json
  export PREV_RUN_CHECKPOINT=
elif [[ "${PREV_RUN_CHECKPOINT+x}" == "x" ]]; then
  if [[ -z "${PREV_RUN_CHECKPOINT}" ]]; then
    echo "PREV_RUN_CHECKPOINT empty — first continue-B from S5 LoRA (new Adam; no HF resume)"
  else
    echo "Explicit PREV_RUN_CHECKPOINT=${PREV_RUN_CHECKPOINT}"
  fi
elif [[ -d /workspace/checkpoints_sota ]]; then
  unset PREV_RUN_CHECKPOINT
  echo "PREV_RUN_CHECKPOINT unset — auto-resume highest complete checkpoint-* (continue hyperparams kept)"
else
  export PREV_RUN_CHECKPOINT=
  echo "No checkpoints_sota — first continue-B from S5 LoRA (new Adam)"
fi

cd /workspace
mkdir -p "$HF_HOME"

if ! python3 -c "import unsloth" 2>/dev/null; then
  echo "Installing Unsloth (first boot)..."
  python3 -u /workspace/train_cpt_sota.py --install
fi

if pgrep -f "train_cpt_sota.py" >/dev/null 2>&1; then
  echo "train_cpt_sota.py already running"
  exit 0
fi

nohup python3 -u /workspace/train_cpt_sota.py > /workspace/cpt_train.log 2>&1 &
echo "Started PID $! — tail -f /workspace/cpt_train.log"
sleep 5
tail -n 80 /workspace/cpt_train.log
