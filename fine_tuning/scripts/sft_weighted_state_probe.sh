#!/usr/bin/env bash
# Compact train/setup state probe for RunPod/Vast monitors (avoid huge ssh argv).
set +e
PIDFILE=/workspace/sft_train.pid
EXITFILE=/workspace/sft_train.exit
SETUPLOG=/workspace/sft_setup.log
LAUNCHLOG=/workspace/sft_launch.log
SMOKELOG=/workspace/sft_smoke.log
TRAINLOG=/workspace/sft_train.log
TRAIN_FRESH_SEC=600
GPU_BUSY_MIB=2048
now=$(date +%s)
if [ -f "$SETUPLOG" ]; then
  echo "SETUP_MTIME=$(stat -c %Y "$SETUPLOG" 2>/dev/null || echo 0)"
  echo "SETUP_SIZE=$(wc -c < "$SETUPLOG" | tr -d ' \n')"
else
  echo "SETUP_MTIME=0"
  echo "SETUP_SIZE=0"
fi
if [ -f "$TRAINLOG" ]; then
  echo "TRAIN_MTIME=$(stat -c %Y "$TRAINLOG" 2>/dev/null || echo 0)"
  echo "TRAIN_SIZE=$(wc -c < "$TRAINLOG" | tr -d ' \n')"
else
  echo "TRAIN_MTIME=0"
  echo "TRAIN_SIZE=0"
fi
if [ -f /workspace/sft_setup_markers.sh ]; then
  # shellcheck disable=SC1091
  . /workspace/sft_setup_markers.sh
else
  actionable_setup_failed_in() {
    local f="$1"
    [ -f "$f" ] || return 1
    grep -qE '^SETUP_FAILED rc=[0-9]+([[:space:]]|$)' "$f" 2>/dev/null
  }
  actionable_smoke_failed_in() {
    local f="$1"
    [ -f "$f" ] || return 1
    grep -qE '^SMOKE_BEFORE_TRAIN_FAILED([[:space:]]|$)' "$f" 2>/dev/null
  }
  first_trigger_line_in() {
    local f="$1"
    local line=""
    [ -f "$f" ] || return 1
    line="$(grep -E '^(SETUP_FAILED rc=[0-9]+|SMOKE_BEFORE_TRAIN_FAILED)([[:space:]]|$)' "$f" 2>/dev/null | head -n 1 || true)"
    [ -n "$line" ] || return 1
    printf '%s\n' "$line"
  }
fi
for f in "$SETUPLOG" "$LAUNCHLOG" "$SMOKELOG"; do
  if [ -f "$f" ] && actionable_smoke_failed_in "$f"; then
    echo "FAIL_MARKER=SMOKE_BEFORE_TRAIN_FAILED"
    echo "TRIGGER_LINE=$(first_trigger_line_in "$f")"
    echo "WEIGHTED_STATE=SMOKE_BEFORE_TRAIN_FAILED"
    exit 0
  fi
done
for f in "$SETUPLOG" "$LAUNCHLOG"; do
  if actionable_setup_failed_in "$f"; then
    echo "FAIL_MARKER=SETUP_FAILED"
    echo "TRIGGER_LINE=$(first_trigger_line_in "$f")"
    echo "WEIGHTED_STATE=SETUP_FAILED"
    exit 0
  fi
done
if grep -qE '^SMOKE_ONLY_DONE' "$SETUPLOG" 2>/dev/null || grep -qE '^SMOKE_ONLY_DONE' "$SMOKELOG" 2>/dev/null; then
  if [ -f "$EXITFILE" ]; then
    echo "WEIGHTED_STATE=SMOKE_ONLY_DONE"
    exit 0
  fi
fi
if [ -f "$PIDFILE" ]; then
  echo "PIDFILE=1"
  pid=$(tr -d ' \n\r' < "$PIDFILE")
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    echo "WEIGHTED_STATE=ALIVE"
    echo "ALIVE_REASON=pidfile"
    exit 0
  fi
else
  echo "PIDFILE=0"
fi
if [ -f "$EXITFILE" ]; then
  echo "EXIT_RC=$(tr -d ' \n\r' < "$EXITFILE")"
  echo "WEIGHTED_STATE=DEAD"
  echo "DEAD_REASON=exitfile"
  exit 0
fi
if pgrep -f "[b]ash /workspace/sft_remote_train_s8_weighted.sh" >/dev/null 2>&1 \
   || pgrep -f "[t]rain_sft_sota.py" >/dev/null 2>&1; then
  echo "WEIGHTED_STATE=ALIVE"
  echo "ALIVE_REASON=pgrep"
  exit 0
fi
if [ -f "$TRAINLOG" ]; then
  train_mtime=$(stat -c %Y "$TRAINLOG" 2>/dev/null || echo 0)
  train_age=$((now - train_mtime))
  if [ "$train_age" -lt "$TRAIN_FRESH_SEC" ]; then
    echo "WEIGHTED_STATE=ALIVE"
    echo "ALIVE_REASON=train_log_fresh age=${train_age}"
    exit 0
  fi
fi
gpu_mib=""
if command -v nvidia-smi >/dev/null 2>&1; then
  gpu_mib=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -n 1 | tr -d ' ')
fi
if [ -n "$gpu_mib" ] && [ "$gpu_mib" -gt "$GPU_BUSY_MIB" ] 2>/dev/null; then
  if grep -q 'FULL_TRAIN' "$SETUPLOG" 2>/dev/null || [ -f "$TRAINLOG" ]; then
    echo "WEIGHTED_STATE=ALIVE"
    echo "ALIVE_REASON=gpu_mem_mib=${gpu_mib}"
    exit 0
  fi
fi
if [ ! -f "$PIDFILE" ]; then
  echo "WEIGHTED_STATE=UNKNOWN"
  exit 0
fi
if grep -q 'FULL_TRAIN' "$SETUPLOG" 2>/dev/null; then
  if [ -f "$TRAINLOG" ]; then
    echo "WEIGHTED_STATE=DEAD"
    echo "DEAD_REASON=train_log_stale_after_full_train"
    exit 0
  fi
  echo "WEIGHTED_STATE=UNKNOWN"
  exit 0
fi
if [ -f "$SETUPLOG" ]; then
  mtime=$(stat -c %Y "$SETUPLOG" 2>/dev/null || echo 0)
  age=$((now - mtime))
  if [ "$age" -lt 180 ]; then
    echo "WEIGHTED_STATE=UNKNOWN"
    exit 0
  fi
fi
echo "WEIGHTED_STATE=DEAD"
echo "DEAD_REASON=pid_gone_setup_stale"
