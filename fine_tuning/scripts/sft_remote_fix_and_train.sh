#!/usr/bin/env bash
set -euo pipefail
source /workspace/.sft_env 2>/dev/null || true
export HF_HOME=/workspace/hf_home
export SFT_WORK_ROOT=/workspace
export USE_CPT_MERGE=1
export SFT_GATE0_MERGED=/workspace/theology_cpt_v2_merged_hf
export PYTHONUNBUFFERED=1

echo "Installing torch 2.11.0+cu126..."
python3 -m pip install -q --break-system-packages \
  torch==2.11.0 torchvision torchaudio \
  --index-url https://download.pytorch.org/whl/cu126

python3 <<'PY'
import torch
print("torch", torch.__version__)
from torch.nn.functional import ScalingType
print("ScalingType OK", ScalingType)
from trl import SFTConfig, SFTTrainer
print("trl OK")
PY

pkill -f train_sft_sota.py 2>/dev/null || true
sleep 2
: > /workspace/sft_train.log
echo "===== relaunch $(date -Is) =====" >> /workspace/sft_train.log
nohup python3 -u /workspace/train_sft_sota.py >> /workspace/sft_train.log 2>&1 &
echo "train_pid $!"
sleep 15
pgrep -af train_sft_sota.py || true
tail -20 /workspace/sft_train.log
