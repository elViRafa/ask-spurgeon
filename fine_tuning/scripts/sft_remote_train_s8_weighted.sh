#!/usr/bin/env bash
# Weighted SFT: frozen RAG mix + open-theology slice on the S8 merged CPT base.
# Does not merge Hub LoRA v2. Does not upload. Does not continue CPT.
# Does not train on open_theology_eval.jsonl.
# Supervisor stays alive (wait on python) and writes sft_train.pid / sft_train.exit
# so the Vast monitor can distinguish ALIVE / DEAD / UNKNOWN.
# Runs a 2-step smoke on longest rows before full train; failed smoke exits so
# the orchestrator can evidence+destroy (failed rental under ~$0.25).
set -euo pipefail

PIDFILE=/workspace/sft_train.pid
EXITFILE=/workspace/sft_train.exit
SETUPLOG=/workspace/sft_setup.log
SMOKELOG=/workspace/sft_smoke.log

# Network volume keeps prior-run smoke fail markers; clear before this supervisor starts
# so the monitor cannot false-trigger SMOKE_BEFORE_TRAIN_FAILED mid-setup.
: > "$SMOKELOG"
rm -rf /workspace/sft_smoke_fail
rm -f "$EXITFILE"

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
if [[ -f /workspace/.sft_isolated_env ]]; then
  # shellcheck disable=SC1091
  source /workspace/.sft_isolated_env
fi
# Force clean CUDA host libs (SIGSEGV class on Vast).
unset LD_LIBRARY_PATH || true
export PYTHONFAULTHANDLER=1

# Force the S8 weighted contract after source. GATE-0 inject writes theology_cpt_v2.
export USE_CPT_MERGE=1
export SFT_GATE0_MERGED=/workspace/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit
export SFT_BASE_REPO=rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit
export SFT_WORK_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export PYTHONUNBUFFERED=1
export SFT_EXPORT=0
export SFT_GPU_PROFILE=4090
# Default peft (Vast). RunPod Unsloth sets SFT_BACKEND=unsloth before launch / in .sft_env.
_backend_in="${SFT_BACKEND:-peft}"
_backend_in="$(echo "$_backend_in" | tr '[:upper:]' '[:lower:]')"
case "$_backend_in" in
  unsloth|peft) export SFT_BACKEND="$_backend_in" ;;
  *)
    echo "REFUSING unknown SFT_BACKEND=${_backend_in} (want peft|unsloth)"
    exit 2
    ;;
esac
# Default seq; smoke retries may lower to 2048 then restore for full train.
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
unset SFT_CPT_ADAPTER || true

# expandable_segments is toggleable (smoke retries may turn it off).
apply_expandable() {
  local on="$1"
  if [[ "$on" == "1" ]]; then
    export SFT_EXPANDABLE_SEGMENTS=1
    export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
  else
    export SFT_EXPANDABLE_SEGMENTS=0
    unset PYTORCH_CUDA_ALLOC_CONF || true
  fi
  echo "SFT_EXPANDABLE_SEGMENTS=${SFT_EXPANDABLE_SEGMENTS} PYTORCH_CUDA_ALLOC_CONF=${PYTORCH_CUDA_ALLOC_CONF:-<unset>}"
}
apply_expandable "${SFT_EXPANDABLE_SEGMENTS:-1}"

resolve_python() {
  if [[ -n "${SFT_PYTHON:-}" && -x "${SFT_PYTHON}" ]]; then
    echo "$SFT_PYTHON"
    return 0
  fi
  if [[ -x /workspace/sft_python ]]; then
    echo /workspace/sft_python
    return 0
  fi
  if [[ -x /workspace/sft_venv/bin/python ]]; then
    echo /workspace/sft_venv/bin/python
    return 0
  fi
  if [[ -x /workspace/miniforge3/envs/sft_train/bin/python ]]; then
    echo /workspace/miniforge3/envs/sft_train/bin/python
    return 0
  fi
  command -v python3
}

{
  echo "=== weighted setup start $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  echo "S8 weighted SFT base ${SFT_GATE0_MERGED}"
  echo "S8 weighted SFT repo ${SFT_BASE_REPO}"
  echo "SFT_BACKEND=${SFT_BACKEND} SFT_EXPORT=${SFT_EXPORT}"
  echo "SFT_OPEN_THEOLOGY=${SFT_OPEN_THEOLOGY} REPEAT=${SFT_OPEN_THEOLOGY_REPEAT}"
  echo "SFT_OUTPUT_DIR=${SFT_OUTPUT_DIR}"
  echo "SUPERVISOR_PID=$(cat "$PIDFILE")"
  echo "LD_LIBRARY_PATH=<unset after explicit unset>"
  echo "PYTHONFAULTHANDLER=${PYTHONFAULTHANDLER}"

  if [[ "${SFT_GATE0_MERGED}" == *theology_cpt_v2_merged_hf* ]]; then
    echo "REFUSING Hub v2 merge path"
    exit 2
  fi
  if [[ "${SFT_OUTPUT_DIR}" == *spurgeon_qa_lora_v2* ]]; then
    echo "REFUSING GATE-0 output dir"
    exit 2
  fi

  # Ship constraints next to setup if sparse sync left it under scripts/.
  if [[ ! -f /workspace/sft_gate0_sep6_constraints.txt ]]; then
    if [[ -f /workspace/ask-spurgeon-src/fine_tuning/scripts/sft_gate0_sep6_constraints.txt ]]; then
      cp /workspace/ask-spurgeon-src/fine_tuning/scripts/sft_gate0_sep6_constraints.txt \
        /workspace/sft_gate0_sep6_constraints.txt
    fi
  fi

  bash /workspace/sft_remote_setup.sh
  # shellcheck disable=SC1091
  source /workspace/.sft_isolated_env 2>/dev/null || true
  unset LD_LIBRARY_PATH || true

  PY="$(resolve_python)"
  echo "TRAIN_PYTHON=$PY"
  "$PY" - <<'PY'
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

  echo "=== TOKENIZER_CPU_SMOKE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  # Fail here, before GPU smoke. SETUP_FAILED rc= is the monitor's anchored marker.
  if ! "$PY" -u /workspace/sft_tokenizer_cpu_smoke.py \
      --base "${SFT_GATE0_MERGED}" \
      --dataprep "${SFT_GATE0_MERGED}"; then
    echo "SETUP_FAILED rc=1"
    exit 1
  fi

  mkdir -p /workspace/sft_s8_weighted/adapter

  cd /workspace
  "$PY" -X faulthandler -u /workspace/train_sft_sota.py --preflight
  echo "=== weighted setup/preflight done $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
} 2>&1 | tee -a "$SETUPLOG"

# shellcheck disable=SC1091
source /workspace/.sft_isolated_env 2>/dev/null || true
unset LD_LIBRARY_PATH || true
PY="$(resolve_python)"

if pgrep -f "[t]rain_sft_sota.py" >/dev/null 2>&1; then
  echo "train_sft_sota.py already running"
  exit 0
fi

run_smoke() {
  local expand="$1"
  local seq="$2"
  local label="$3"
  echo "=== SMOKE_BEFORE_TRAIN label=${label} expandable=${expand} seq=${seq} $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$SETUPLOG" "$SMOKELOG"
  apply_expandable "$expand"
  export SFT_MAX_SEQ_LENGTH="$seq"
  export SFT_SMOKE=1
  export SFT_MAX_STEPS=2
  export SFT_FORCE_DATAPREP=1
  # CUDA_LAUNCH_BLOCKING only during smoke (syncs kernels for clearer faults).
  export CUDA_LAUNCH_BLOCKING=1
  set +e
  "$PY" -X faulthandler -u /workspace/train_sft_sota.py --smoke >> "$SMOKELOG" 2>&1
  local rc=$?
  set -e
  unset CUDA_LAUNCH_BLOCKING || true
  unset SFT_SMOKE || true
  unset SFT_MAX_STEPS || true
  echo "SMOKE_EXIT label=${label} rc=${rc}" | tee -a "$SETUPLOG" "$SMOKELOG"
  if [[ $rc -eq 0 ]] && grep -qE 'SFT_SMOKE_PASS|SOTA SFT v2 complete' "$SMOKELOG"; then
    # Accept legacy Unsloth runs that finished train but omitted SFT_SMOKE_PASS
    # (fixed in train_sft_sota.py _train_unsloth). Prefer explicit SFT_SMOKE_PASS.
    if ! grep -q "SFT_SMOKE_PASS" "$SMOKELOG"; then
      echo "SFT_SMOKE_PASS steps=${SFT_MAX_STEPS:-2} (inferred from SOTA SFT v2 complete)" | tee -a "$SMOKELOG" "$SETUPLOG"
    fi
    echo "SMOKE_OK label=${label}" | tee -a "$SETUPLOG"
    return 0
  fi

  if [[ $rc -eq 139 ]]; then
    echo "SMOKE_FAIL sigsegv_exit_139 label=${label}" | tee -a "$SETUPLOG"
  else
    echo "SMOKE_FAIL rc=${rc} label=${label}" | tee -a "$SETUPLOG"
  fi
  return 1
}

SMOKE_EXPAND=1
SMOKE_SEQ=4608
SMOKE_OK=0
if run_smoke 1 4608 "expand_on_seq4608"; then
  SMOKE_OK=1
  SMOKE_EXPAND=1
  SMOKE_SEQ=4608
elif run_smoke 0 4608 "expand_off_seq4608"; then
  SMOKE_OK=1
  SMOKE_EXPAND=0
  SMOKE_SEQ=4608
elif run_smoke 0 2048 "expand_off_seq2048"; then
  SMOKE_OK=1
  SMOKE_EXPAND=0
  SMOKE_SEQ=2048
fi

if [[ "$SMOKE_OK" != "1" ]]; then
  # Whole line so ^SMOKE_BEFORE_TRAIN_FAILED$ matches. Also written to the smoke log.
  echo "SMOKE_BEFORE_TRAIN_FAILED" | tee -a "$SETUPLOG" "$SMOKELOG"
  echo "smoke failed; leaving logs for evidence; aborting before full train" | tee -a "$SETUPLOG"
  mkdir -p /workspace/sft_smoke_fail
  {
    echo "smoke_failed=1"
    echo "utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "see=/workspace/sft_smoke.log"
  } > /workspace/sft_smoke_fail/status.txt
  tail -n 100 "$SMOKELOG" >> /workspace/sft_smoke_fail/status.txt || true
  # Non-zero exit so the monitor's marker path can evidence and destroy.
  exit 1
fi

# Full train uses the smoke-proven expandable/seq settings.
apply_expandable "$SMOKE_EXPAND"
export SFT_MAX_SEQ_LENGTH="$SMOKE_SEQ"
unset CUDA_LAUNCH_BLOCKING || true
unset SFT_SMOKE || true
unset SFT_MAX_STEPS || true
export SFT_FORCE_DATAPREP=1

# RunPod Unsloth path: orchestrator -SmokeOnly sets SFT_SMOKE_ONLY=1 to measure s/step
# without committing to the full ~514-step train.
if [[ "${SFT_SMOKE_ONLY:-0}" == "1" ]]; then
  echo "SMOKE_ONLY_DONE expandable=${SMOKE_EXPAND} seq=${SMOKE_SEQ} backend=${SFT_BACKEND}" | tee -a "$SETUPLOG" "$SMOKELOG"
  exit 0
fi

echo "FULL_TRAIN expandable=${SMOKE_EXPAND} seq=${SMOKE_SEQ}" | tee -a "$SETUPLOG"

"$PY" -X faulthandler -u /workspace/train_sft_sota.py > /workspace/sft_train.log 2>&1 &
TRAIN_PID=$!
echo "Started TRAIN_PID $TRAIN_PID — supervisor PID $(tr -d ' \n' < "$PIDFILE")" | tee -a "$SETUPLOG"
# Keep supervisor (this bash) alive so sft_train.pid stays valid for the whole job.
wait "$TRAIN_PID"
rc=$?
echo "TRAIN_EXIT $rc" | tee -a "$SETUPLOG"
exit "$rc"
