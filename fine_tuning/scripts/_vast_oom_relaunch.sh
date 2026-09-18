#!/bin/bash
# Emergency relaunch after eval CUDA OOM at step 20. Never echo secrets.
set -euo pipefail
cd /workspace

# Append eval-off without printing secrets
if ! grep -q 'SFT_EVAL_STRATEGY' /workspace/.sft_env 2>/dev/null; then
  printf '%s\n' \
    'export SFT_EVAL_STRATEGY=no' \
    'export SFT_PER_DEVICE_EVAL_BATCH=1' \
    'export SFT_SAVE_STEPS=40' >> /workspace/.sft_env
fi

# Rotate crash log so monitor does not see OOM tail
if [ -f /workspace/sft_train.log ]; then
  mv /workspace/sft_train.log /workspace/sft_train_oom_step20.log
fi

pkill -f 'train_sft_sota.py' 2>/dev/null || true
sleep 2

set -a
# shellcheck disable=SC1091
source /workspace/.sft_env
set +a
export SFT_BACKEND=peft
export SFT_MAX_SEQ_LENGTH=2048
export SFT_PER_DEVICE_BATCH=1
export SFT_GRAD_ACCUM=16
export SFT_EVAL_STRATEGY=no
export SFT_PER_DEVICE_EVAL_BATCH=1
export SFT_SAVE_STEPS=40
export CUDA_VISIBLE_DEVICES=0
export TORCHDYNAMO_DISABLE=1
export TORCH_COMPILE_DISABLE=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# Confirm eval fix is in synced script (no secrets)
grep -n 'SFT_EVAL_STRATEGY\|_eval_strategy\|empty_cache' /workspace/train_sft_sota.py | head -20

# No checkpoint to resume (died before save_steps=40)
nohup python3 -u /workspace/train_sft_sota.py > /workspace/sft_train.log 2>&1 &
echo "RELAUNCH_PID=$!"
sleep 12
grep -E '^export SFT_(BACKEND|MAX_SEQ|PER_DEVICE|GRAD_ACCUM|EVAL_|SAVE_)' /workspace/.sft_env || true
head -n 50 /workspace/sft_train.log || true
pgrep -af 'train_sft_sota.py' || true
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv
