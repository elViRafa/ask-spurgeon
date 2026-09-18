#!/usr/bin/env bash
# On-pod launcher for SFT GATE-0: setup -> merge -> train (detached).
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

if [[ "${SFT_GPU_PROFILE:-}" == "a16" ]]; then
  export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
  export SFT_PER_DEVICE_BATCH="${SFT_PER_DEVICE_BATCH:-1}"
  export SFT_GRAD_ACCUM="${SFT_GRAD_ACCUM:-16}"
  echo "A16 train env BATCH=${SFT_PER_DEVICE_BATCH} GRAD_ACCUM=${SFT_GRAD_ACCUM} CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES}"
elif [[ "${SFT_GPU_PROFILE:-}" == "4090" ]]; then
  export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
  export SFT_PER_DEVICE_BATCH="${SFT_PER_DEVICE_BATCH:-2}"
  export SFT_GRAD_ACCUM="${SFT_GRAD_ACCUM:-8}"
  echo "4090 train env BATCH=${SFT_PER_DEVICE_BATCH} GRAD_ACCUM=${SFT_GRAD_ACCUM} CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES}"
fi

cd /workspace
mkdir -p "$HF_HOME"

bash /workspace/sft_remote_setup.sh

if [[ ! -f "$SFT_GATE0_MERGED/config.json" ]]; then
  echo "===== GATE-0 merge ====="
  bash /workspace/sft_remote_merge.sh
fi

if ! python3 -c "import unsloth" 2>/dev/null; then
  echo "Installing Unsloth for SFT..."
  python3 -u /workspace/train_sft_sota.py --install
fi

python3 -u /workspace/train_sft_sota.py --preflight

if pgrep -f "train_sft_sota.py" >/dev/null 2>&1; then
  echo "train_sft_sota.py already running"
  exit 0
fi

nohup python3 -u /workspace/train_sft_sota.py > /workspace/sft_train.log 2>&1 &
echo "Started PID $! — tail -f /workspace/sft_train.log"
sleep 5
tail -n 80 /workspace/sft_train.log
