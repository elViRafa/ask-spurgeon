#!/usr/bin/env bash
# Merge weighted S8 SFT LoRA (reuse staging if present), then evaluate.py generate-only
# against open_theology_eval.jsonl. Judge runs on the PC (evaluate_open_theology.py).
# SFT_EXPORT=0. Never promotes Hub/Ollama.
set -euo pipefail

export SFT_WORK_ROOT="${SFT_WORK_ROOT:-/workspace}"
export HF_HOME="${HF_HOME:-/workspace/hf_home}"
export PYTHONUNBUFFERED=1
export USE_CPT_MERGE=1
export SFT_EXPORT=0
export SFT_GATE0_MERGED="${SFT_GATE0_MERGED:-/workspace/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit}"
export SFT_BASE_REPO="${SFT_BASE_REPO:-rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit}"
export SFT_LORA_DIR="${SFT_LORA_DIR:-/workspace/sft_s8_weighted/adapter/lora}"
export SFT_MERGED_OUT="${SFT_MERGED_OUT:-/workspace/spurgeon_qa_s8w_merged_hf}"
export SFT_LORA_HUB="${SFT_LORA_HUB:-}"
EVAL_ROOT="${SFT_EVAL_ROOT:-/workspace/ask-spurgeon-eval}"
SCRIPTS="$EVAL_ROOT/fine_tuning/scripts"
OT_EVAL="${SFT_OT_EVAL_SET:-/workspace/open_theology_eval.jsonl}"
OUT_REPORT="${SFT_OT_GEN_REPORT:-/workspace/open_theology_eval_s8_weighted.gen.json}"
LIMIT="${SFT_EVAL_LIMIT:-0}"
ADAPTER_WEIGHTS="${SFT_LORA_DIR}/adapter_model.safetensors"

cd /workspace

echo "OT_EVAL_BEGIN lora=$SFT_LORA_DIR base=$SFT_GATE0_MERGED merged=$SFT_MERGED_OUT eval=$OT_EVAL"

if [[ ! -f "$ADAPTER_WEIGHTS" ]]; then
  echo "ERROR: missing adapter at $SFT_LORA_DIR" >&2
  exit 2
fi
if [[ ! -f "$SCRIPTS/evaluate.py" || ! -f "$EVAL_ROOT/config.py" ]]; then
  echo "ERROR: eval tree missing under $EVAL_ROOT" >&2
  exit 2
fi
if [[ ! -f "$OT_EVAL" ]]; then
  echo "ERROR: open theology eval set missing: $OT_EVAL" >&2
  exit 2
fi

if [[ ! -f "$SFT_GATE0_MERGED/config.json" ]]; then
  echo "Downloading S8 merged base from Hub: $SFT_BASE_REPO"
  python3 - <<'PY'
import os
from pathlib import Path
from huggingface_hub import snapshot_download

repo = os.environ["SFT_BASE_REPO"]
dest = Path(os.environ["SFT_GATE0_MERGED"])
dest.parent.mkdir(parents=True, exist_ok=True)
token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
snapshot_download(
    repo_id=repo,
    local_dir=str(dest),
    token=token,
    ignore_patterns=["*.md", "*.gguf", ".gitattributes"],
)
print("BASE_DOWNLOAD_OK", dest)
PY
fi
test -f "$SFT_GATE0_MERGED/config.json"

if [[ -f "$SFT_MERGED_OUT/config.json" ]]; then
  echo "SFT_MERGE_REUSE $SFT_MERGED_OUT"
else
  python3 -u "$SCRIPTS/merge_sft_lora.py" --install
  python3 -u "$SCRIPTS/merge_sft_lora.py"
  test -f "$SFT_MERGED_OUT/config.json"
  echo "SFT_MERGE_OK $SFT_MERGED_OUT"
fi

python3 - <<'PY'
import importlib
import subprocess
import sys

need = []
for mod in ("dotenv", "transformers", "peft", "safetensors"):
    try:
        importlib.import_module(mod if mod != "dotenv" else "dotenv")
    except ImportError:
        need.append(mod if mod != "dotenv" else "python-dotenv")
if need:
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-q",
            "--break-system-packages",
            "python-dotenv",
            "transformers>=4.51.0",
            "peft",
            "accelerate",
            "safetensors",
            "huggingface_hub",
            "sentencepiece",
            "protobuf",
        ]
    )
print("EVAL_DEPS_OK")
PY

LIMIT_ARGS=()
if [[ "$LIMIT" != "0" && -n "$LIMIT" ]]; then
  LIMIT_ARGS=(--limit "$LIMIT")
fi

# Generate only — no --judge (Groq/Gemini often 403 from datacenter; OT judge is absolute on PC).
# evaluate.py still computes RAG F §5 gates and may exit 1 on this answerable-only set;
# treat a written report as success (OT scoring is separate / release_gate=false).
set +e
python3 -u "$SCRIPTS/evaluate.py" \
  --candidate "hf:${SFT_MERGED_OUT}" \
  --baseline none \
  --test-set "$OT_EVAL" \
  --output "$OUT_REPORT" \
  --source-adapter-artifact "$ADAPTER_WEIGHTS" \
  --max-tokens 500 \
  "${LIMIT_ARGS[@]}"
gen_rc=$?
set -e
if [[ ! -f "$OUT_REPORT" ]]; then
  echo "ERROR: evaluate.py exited $gen_rc and wrote no report" >&2
  exit "$gen_rc"
fi
echo "OT_GEN_OK rc=$gen_rc report=$OUT_REPORT"
