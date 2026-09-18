#!/usr/bin/env bash
# On Vast: ensure CPT-merged HF exists, then PEFT-merge SFT LoRA -> spurgeon_qa_merged_hf.
set -euo pipefail

if [[ -f /workspace/.sft_env ]]; then
  # shellcheck disable=SC1091
  source /workspace/.sft_env
fi

export SFT_WORK_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export PYTHONUNBUFFERED=1
export SFT_GATE0_MERGED="${SFT_GATE0_MERGED:-/workspace/theology_cpt_v2_merged_hf}"
export SFT_LORA_DIR="${SFT_LORA_DIR:-/workspace/spurgeon_qa_lora_v2/lora}"
export SFT_MERGED_OUT="${SFT_MERGED_OUT:-/workspace/spurgeon_qa_merged_hf}"
export SFT_LORA_HUB="${SFT_LORA_HUB:-rafaelvieirar1r/qwen3.5-4b-spurgeon-qa-lora-v2}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

cd /workspace
mkdir -p "$HF_HOME"

if [[ ! -f "$SFT_GATE0_MERGED/config.json" ]]; then
  echo "CPT-merged missing — running GATE-0 CPT merge first..."
  bash /workspace/sft_remote_merge.sh
fi

if [[ ! -f "$SFT_GATE0_MERGED/config.json" ]]; then
  echo "FATAL: CPT-merged still missing after remake"
  exit 1
fi

if [[ -f "$SFT_MERGED_OUT/config.json" ]]; then
  echo "SFT merged HF already exists — skip"
  ls -lah "$SFT_MERGED_OUT" | head -20
  exit 0
fi

python3 -u /workspace/merge_sft_lora.py --install
python3 -u /workspace/merge_sft_lora.py
echo "SFT_MERGE_PIPELINE_DONE"
ls -lah "$SFT_MERGED_OUT" | head -30
