#!/usr/bin/env bash
# GATE-0 merge only: Hub v2 LoRA -> theology_cpt_v2_merged_hf on volume.
set -euo pipefail

if [[ -f /workspace/.sft_env ]]; then
  # shellcheck disable=SC1091
  source /workspace/.sft_env
fi

export SFT_WORK_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export PYTHONUNBUFFERED=1
export SFT_CPT_ADAPTER=/workspace/theology_cpt_lora_hub_v2
export SFT_GATE0_MERGED=/workspace/theology_cpt_v2_merged_hf
export EXPECTED_ADAPTER_SHA256=319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478

if [[ "${SFT_GPU_PROFILE:-}" == "a16" ]]; then
  export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
fi

cd /workspace
mkdir -p "$HF_HOME"

if [[ -f "$SFT_GATE0_MERGED/config.json" ]]; then
  echo "GATE-0 merged HF already exists — skip merge"
  if [[ -f /workspace/verify_sft_stop_tokens.py && "${SFT_SKIP_STOP_PHASE2:-0}" != "1" ]]; then
    echo "Running stop-token phase 2 (CPT merged base probe)..."
    if ! python3 -u /workspace/verify_sft_stop_tokens.py \
      --phase 2 \
      --base "$SFT_GATE0_MERGED" \
      --out /workspace/stop_token_phase2.json; then
      echo "WARN: phase 2 stop probe failed — continuing (SFT teaches im_end stop)"
    fi
  fi
  exit 0
fi

if ! python3 -c "import unsloth" 2>/dev/null; then
  echo "Installing Unsloth (first boot)..."
  python3 -u /workspace/merge_cpt_lora.py --install
fi

python3 -u /workspace/merge_cpt_lora.py --preflight
python3 -u /workspace/merge_cpt_lora.py
echo "MERGE_DONE"

if [[ -f /workspace/verify_sft_stop_tokens.py && -f "$SFT_GATE0_MERGED/config.json" ]]; then
  if [[ "${SFT_SKIP_STOP_PHASE2:-0}" != "1" ]]; then
    echo "Running stop-token phase 2 (CPT merged base probe)..."
    if ! python3 -u /workspace/verify_sft_stop_tokens.py \
      --phase 2 \
      --base "$SFT_GATE0_MERGED" \
      --out /workspace/stop_token_phase2.json; then
      echo "WARN: phase 2 stop probe failed — continuing to SFT (base may not emit im_end until trained)"
    fi
  fi
fi
