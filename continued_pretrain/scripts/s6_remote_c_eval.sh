#!/usr/bin/env bash
# C eval for S6 partial run (best HF checkpoint on volume). Does not touch training checkpoints.
set -euo pipefail

BEST_CKPT="${S6_EVAL_CHECKPOINT:-/workspace/checkpoints_sota/checkpoint-2050}"
WORK=/workspace
LORA="$WORK/theology_cpt_lora"
BACKUP="$WORK/theology_cpt_lora_s5_init_backup"
STAGE="$WORK/theology_cpt_lora_s6_eval_stage"

export CPT_WORK_ROOT=$WORK CPT_DATA_ROOT=$WORK HF_HOME=$WORK/hf_home PYTHONUNBUFFERED=1

if [[ ! -f "$BEST_CKPT/adapter_model.safetensors" ]]; then
  echo "FAIL: missing adapter at $BEST_CKPT"
  exit 1
fi

SHA=$(python3 -c "import hashlib; p='$BEST_CKPT/adapter_model.safetensors'; print(hashlib.sha256(open(p,'rb').read()).hexdigest())")
echo "S6 C eval adapter: $BEST_CKPT"
echo "EXPECTED_ADAPTER_SHA256=$SHA"

# Stage eval adapter without destroying S5 init backup on volume
if [[ ! -d "$BACKUP" && -d "$LORA" ]]; then
  echo "Backing up current theology_cpt_lora -> theology_cpt_lora_s5_init_backup"
  cp -a "$LORA" "$BACKUP"
fi
rm -rf "$STAGE"
mkdir -p "$STAGE"
for f in adapter_model.safetensors adapter_config.json tokenizer.json tokenizer_config.json README.md; do
  if [[ -f "$BEST_CKPT/$f" ]]; then
    cp -a "$BEST_CKPT/$f" "$STAGE/"
  fi
done
rm -rf "$LORA"
cp -a "$STAGE" "$LORA"

export EXPECTED_ADAPTER_SHA256="$SHA"

cd "$WORK"
if ! python3 -c "import unsloth" 2>/dev/null; then
  echo "Installing deps via eval --install..."
  python3 -u /workspace/eval_cpt_sota.py --install
fi

python3 -u /workspace/eval_cpt_sota.py --preflight
nohup python3 -u /workspace/eval_cpt_sota.py > /workspace/cpt_eval.log 2>&1 &
echo "C eval PID $! — tail -f /workspace/cpt_eval.log"
sleep 8
tail -n 40 /workspace/cpt_eval.log
