#!/usr/bin/env bash
# SFT on the already-merged S8 CPT weights. Does not merge Hub LoRA v2.
# Does not upload. Does not continue CPT.
set -euo pipefail

if [[ -f /workspace/.sft_env ]]; then
  # shellcheck disable=SC1091
  source /workspace/.sft_env
fi

# Force the S8 base after source. A GATE-0 inject writes theology_cpt_v2.
export USE_CPT_MERGE=1
export SFT_GATE0_MERGED=/workspace/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit
export SFT_BASE_REPO=rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit
export SFT_WORK_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export PYTHONUNBUFFERED=1
export SFT_EXPORT=0
export SFT_GPU_PROFILE=4090
export SFT_BACKEND=peft
export SFT_MAX_SEQ_LENGTH=2048
export SFT_PER_DEVICE_BATCH=1
export SFT_GRAD_ACCUM=16
export SFT_EVAL_STRATEGY=no
export SFT_SAVE_STEPS=40
export CUDA_VISIBLE_DEVICES=0
export UNSLOTH_COMPILE_DISABLE=1
export UNSLOTH_DISABLE_FAST_GENERATION=1
export TORCHDYNAMO_DISABLE=1
export TORCH_COMPILE_DISABLE=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
unset SFT_CPT_ADAPTER || true

echo "S8 SFT base ${SFT_GATE0_MERGED}"
echo "S8 SFT repo ${SFT_BASE_REPO}"
echo "SFT_BACKEND=${SFT_BACKEND} SFT_EXPORT=${SFT_EXPORT}"

if [[ "${SFT_GATE0_MERGED}" == *theology_cpt_v2_merged_hf* ]]; then
  echo "REFUSING Hub v2 merge path"
  exit 2
fi

bash /workspace/sft_remote_setup.sh

python3 - <<'PY'
import os
from pathlib import Path
from huggingface_hub import snapshot_download

dest = Path("/workspace/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit")
if (dest / "config.json").is_file() and (dest / "tokenizer_config.json").is_file():
    print("S8_MERGED_PRESENT", dest)
else:
    snapshot_download(
        repo_id="rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit",
        local_dir=str(dest),
        token=os.environ.get("HF_TOKEN") or None,
    )
    print("S8_MERGED_DOWNLOADED", dest)
if not (dest / "config.json").is_file():
    raise SystemExit("S8 merged config.json missing after download")
PY

cd /workspace
python3 -u /workspace/train_sft_sota.py --preflight

if pgrep -f "train_sft_sota.py" >/dev/null 2>&1; then
  echo "train_sft_sota.py already running"
  exit 0
fi

nohup python3 -u /workspace/train_sft_sota.py > /workspace/sft_train.log 2>&1 &
echo "Started PID $! — tail -f /workspace/sft_train.log"
sleep 5
tail -n 40 /workspace/sft_train.log
