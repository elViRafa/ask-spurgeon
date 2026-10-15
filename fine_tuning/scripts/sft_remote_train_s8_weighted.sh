#!/usr/bin/env bash
# Weighted SFT: frozen RAG mix + open-theology slice on the S8 merged CPT base.
# Does not merge Hub LoRA v2. Does not upload. Does not continue CPT.
# Does not train on open_theology_eval.jsonl.
# Supervisor stays alive (wait on python) and writes sft_train.pid / sft_train.exit
# so the Vast monitor can distinguish ALIVE / DEAD / UNKNOWN.
set -euo pipefail

PIDFILE=/workspace/sft_train.pid
EXITFILE=/workspace/sft_train.exit
SETUPLOG=/workspace/sft_setup.log

echo $$ > "$PIDFILE"
_write_exit() {
  local rc=$?
  echo "$rc" > "$EXITFILE"
}
trap '_write_exit' EXIT

if [[ -f /workspace/.sft_env ]]; then
  # shellcheck disable=SC1091
  source /workspace/.sft_env
fi

# Force the S8 weighted contract after source. GATE-0 inject writes theology_cpt_v2.
export USE_CPT_MERGE=1
export SFT_GATE0_MERGED=/workspace/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit
export SFT_BASE_REPO=rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit
export SFT_WORK_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export PYTHONUNBUFFERED=1
export SFT_EXPORT=0
export SFT_GPU_PROFILE=4090
export SFT_BACKEND=peft
export SFT_MAX_SEQ_LENGTH=4608
export SFT_PER_DEVICE_BATCH=1
export SFT_GRAD_ACCUM=16
export SFT_EVAL_STRATEGY=no
export SFT_SAVE_STEPS=40
export SFT_OPEN_THEOLOGY=1
export SFT_OPEN_THEOLOGY_REPEAT=1
export SFT_FORCE_DATAPREP=1
export SFT_OUTPUT_DIR=/workspace/sft_s8_weighted/adapter
export CUDA_VISIBLE_DEVICES=0
export UNSLOTH_COMPILE_DISABLE=1
export UNSLOTH_DISABLE_FAST_GENERATION=1
export TORCHDYNAMO_DISABLE=1
export TORCH_COMPILE_DISABLE=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
unset SFT_CPT_ADAPTER || true

{
  echo "=== weighted setup start $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  echo "S8 weighted SFT base ${SFT_GATE0_MERGED}"
  echo "S8 weighted SFT repo ${SFT_BASE_REPO}"
  echo "SFT_BACKEND=${SFT_BACKEND} SFT_EXPORT=${SFT_EXPORT}"
  echo "SFT_OPEN_THEOLOGY=${SFT_OPEN_THEOLOGY} REPEAT=${SFT_OPEN_THEOLOGY_REPEAT}"
  echo "SFT_OUTPUT_DIR=${SFT_OUTPUT_DIR}"
  echo "SUPERVISOR_PID=$(cat "$PIDFILE")"

  if [[ "${SFT_GATE0_MERGED}" == *theology_cpt_v2_merged_hf* ]]; then
    echo "REFUSING Hub v2 merge path"
    exit 2
  fi
  if [[ "${SFT_OUTPUT_DIR}" == *spurgeon_qa_lora_v2* ]]; then
    echo "REFUSING GATE-0 output dir"
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

mix = Path("/workspace/spurgeon-qa-mix-v1")
for name in ("qa_mix_train.jsonl", "qa_mix_val.jsonl"):
    if not (mix / name).is_file():
        raise SystemExit(f"missing {mix / name}")
theo = Path("/workspace/qa_open_theology/sft/open_theology_train.jsonl")
if not theo.is_file():
    raise SystemExit(f"missing {theo}")
print("RAG_MIX_OK", mix)
print("OPEN_THEOLOGY_TRAIN_OK", theo)
PY

  mkdir -p /workspace/sft_s8_weighted/adapter

  cd /workspace
  python3 -u /workspace/train_sft_sota.py --preflight
  echo "=== weighted setup/preflight done $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
} 2>&1 | tee -a "$SETUPLOG"

if pgrep -f "[t]rain_sft_sota.py" >/dev/null 2>&1; then
  echo "train_sft_sota.py already running"
  exit 0
fi

python3 -u /workspace/train_sft_sota.py > /workspace/sft_train.log 2>&1 &
TRAIN_PID=$!
echo "Started TRAIN_PID $TRAIN_PID — supervisor PID $(tr -d ' \n' < "$PIDFILE")" | tee -a "$SETUPLOG"
# Keep supervisor (this bash) alive so sft_train.pid stays valid for the whole job.
wait "$TRAIN_PID"
rc=$?
echo "TRAIN_EXIT $rc" | tee -a "$SETUPLOG"
exit "$rc"
