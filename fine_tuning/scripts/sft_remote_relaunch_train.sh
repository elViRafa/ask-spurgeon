#!/usr/bin/env bash
# Fix deps and relaunch SFT train (skip merge if GATE-0 exists).
set -euo pipefail

if [[ -f /workspace/.sft_env ]]; then
  # shellcheck disable=SC1091
  source /workspace/.sft_env
fi

export SFT_WORK_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export PYTHONUNBUFFERED=1
export USE_CPT_MERGE=1
export SFT_GATE0_MERGED=/workspace/theology_cpt_v2_merged_hf

cd /workspace

echo "===== torch upgrade (>=2.11 for torchao/trl) ====="
python3 - <<'PY'
import subprocess, sys
import torch
ver = tuple(int(x) for x in torch.__version__.split("+")[0].split(".")[:2])
print("torch before", torch.__version__)
if ver < (2, 11):
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-q", "--break-system-packages",
        "torch==2.11.0", "torchvision", "torchaudio",
        "--index-url", "https://download.pytorch.org/whl/cu126",
    ])
import torch as t
print("torch after", t.__version__)
from torch.nn.functional import ScalingType  # noqa: F401
print("ScalingType OK")
PY

echo "===== verify trl import ====="
python3 -c "from trl import SFTConfig, SFTTrainer; print('trl OK')"

pkill -f train_sft_sota.py 2>/dev/null || true
sleep 2

: > /workspace/sft_train.log
echo "===== relaunch $(date -Is) =====" >> /workspace/sft_train.log

if pgrep -f train_sft_sota.py >/dev/null 2>&1; then
  echo "train already running"
  exit 0
fi

nohup python3 -u /workspace/train_sft_sota.py >> /workspace/sft_train.log 2>&1 &
echo "Started train PID $!"
sleep 10
pgrep -af train_sft_sota.py || true
tail -25 /workspace/sft_train.log
