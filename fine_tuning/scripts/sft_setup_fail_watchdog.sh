#!/usr/bin/env bash
# Detached remote watchdog: on early setup/smoke failure, keep logs + write evidence,
# then self-destroy the Vast instance so a dead local launcher cannot leave it billing.
# Credentials: /workspace/.sft_watchdog_env (chmod 600) with VAST_API_KEY + VAST_INSTANCE_ID.
# Does NOT destroy once FULL_TRAIN / SETUP_OK+pidfile healthy training is underway.
set -euo pipefail

SETUPLOG=/workspace/sft_setup.log
LAUNCHLOG=/workspace/sft_launch.log
SMOKELOG=/workspace/sft_smoke.log
EXITFILE=/workspace/sft_train.exit
PIDFILE=/workspace/sft_train.pid
EVDIR=/workspace/sft_fail_evidence
WATCH_ENV=/workspace/.sft_watchdog_env
MARKER=/workspace/sft_watchdog_destroyed.marker
MARKERS_SH=/workspace/sft_setup_markers.sh
POLL_SEC="${SFT_WATCHDOG_POLL_SEC:-20}"
# Hard wall must cover long first-time pin install (silent cap ~90m).
MAX_MIN="${SFT_WATCHDOG_MAX_MIN:-90}"
# Base grace before silent fail; extended while setup log advances (see below).
SILENT_FAIL_MIN="${SFT_WATCHDOG_SILENT_FAIL_MIN:-25}"
# Log must be this many seconds stale before silent destroy fires.
SILENT_STALE_SEC="${SFT_WATCHDOG_SILENT_STALE_SEC:-300}"
# Cap on silent deadline extensions while pip/setup is still writing the log.
SILENT_CAP_MIN="${SFT_WATCHDOG_SILENT_CAP_MIN:-90}"

mkdir -p /workspace
echo "WATCHDOG_START utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) poll=${POLL_SEC}s max=${MAX_MIN}m silent=${SILENT_FAIL_MIN}m cap=${SILENT_CAP_MIN}m stale=${SILENT_STALE_SEC}s" | tee -a "$SETUPLOG"

if [[ -f "$WATCH_ENV" ]]; then
  # shellcheck disable=SC1090
  source "$WATCH_ENV"
fi

if [[ -f "$MARKERS_SH" ]]; then
  # shellcheck disable=SC1090
  source "$MARKERS_SH"
else
  echo "WATCHDOG_WARN missing $MARKERS_SH — embedding fallback actionable_setup_failed_in" | tee -a "$SETUPLOG"
  # Fallback kept in sync with sft_setup_markers.sh (contract tests assert both).
  actionable_setup_failed_in() {
    local f="$1"
    [[ -f "$f" ]] || return 1
    grep -q 'SETUP_FAILED' "$f" 2>/dev/null || return 1
    if grep -qE 'SETUP_FAILED[[:space:]]+line=[0-9]+[[:space:]]+reason=' "$f" 2>/dev/null; then
      return 0
    fi
    local pins_line=0 i=0 line
    while IFS= read -r line || [[ -n "$line" ]]; do
      i=$((i + 1))
      case "$line" in
        *SETUP_PINS_OK*|*SETUP_PHASE=pins_ok*) pins_line=$i ;;
      esac
      if [[ "$pins_line" -gt 0 ]] && [[ "$i" -gt "$pins_line" ]] && [[ "$line" == *SETUP_FAILED* ]]; then
        return 0
      fi
    done < "$f"
    return 1
  }
fi

has_fail_marker() {
  local f
  for f in "$SETUPLOG" "$LAUNCHLOG" "$SMOKELOG"; do
    [[ -f "$f" ]] || continue
    if grep -q 'SMOKE_BEFORE_TRAIN_FAILED' "$f" 2>/dev/null; then
      return 0
    fi
  done
  for f in "$SETUPLOG" "$LAUNCHLOG"; do
    if actionable_setup_failed_in "$f"; then
      return 0
    fi
  done
  return 1
}

training_healthy() {
  if [[ -f "$PIDFILE" ]]; then
    local pid
    pid=$(tr -d ' \n\r' < "$PIDFILE" || true)
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      if grep -q 'FULL_TRAIN' "$SETUPLOG" 2>/dev/null; then
        return 0
      fi
      if grep -q 'SETUP_OK' "$SETUPLOG" 2>/dev/null && ! has_fail_marker; then
        return 0
      fi
    fi
  fi
  return 1
}

write_evidence() {
  local reason="$1"
  mkdir -p "$EVDIR"
  {
    echo "reason=$reason"
    echo "utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "hostname=$(hostname 2>/dev/null || true)"
    echo "=== nvidia-smi ==="
    nvidia-smi 2>&1 || true
    echo "=== free -h ==="
    free -h 2>&1 || true
    echo "=== setup tail ==="
    tail -n 200 "$SETUPLOG" 2>/dev/null || true
    echo "=== launch tail ==="
    tail -n 120 "$LAUNCHLOG" 2>/dev/null || true
    echo "=== smoke tail ==="
    tail -n 120 "$SMOKELOG" 2>/dev/null || true
    echo "=== pid/exit ==="
    cat "$PIDFILE" 2>/dev/null || true
    cat "$EXITFILE" 2>/dev/null || true
    echo "=== pip freeze head ==="
    head -n 80 /workspace/sft_pip_freeze.txt 2>/dev/null || true
  } > "$EVDIR/capture.txt"
  cp -f "$SETUPLOG" "$EVDIR/sft_setup.log" 2>/dev/null || true
  cp -f "$LAUNCHLOG" "$EVDIR/sft_launch.log" 2>/dev/null || true
  cp -f "$SMOKELOG" "$EVDIR/sft_smoke.log" 2>/dev/null || true
  cp -f /workspace/sft_pip_freeze.txt "$EVDIR/sft_pip_freeze.txt" 2>/dev/null || true
  echo "evidence_ok=1" > "$EVDIR/status.txt"
  echo "WATCHDOG_EVIDENCE_OK dir=$EVDIR reason=$reason" | tee -a "$SETUPLOG"
}

destroy_self() {
  local reason="$1"
  if [[ -f "$MARKER" ]]; then
    echo "WATCHDOG_ALREADY_DESTROYED" | tee -a "$SETUPLOG"
    return 0
  fi
  write_evidence "$reason"
  local id="${VAST_INSTANCE_ID:-}"
  local key="${VAST_API_KEY:-}"
  if [[ -z "$id" || -z "$key" ]]; then
    echo "WATCHDOG_NO_CREDS cannot self-destroy (missing VAST_INSTANCE_ID or VAST_API_KEY); evidence kept" | tee -a "$SETUPLOG"
    echo "WATCHDOG_NO_CREDS" > "$MARKER"
    return 0
  fi
  echo "WATCHDOG_DESTROY_BEGIN id=$id reason=$reason" | tee -a "$SETUPLOG"
  # Prefer vastai CLI when present; else REST DELETE.
  set +e
  if command -v vastai >/dev/null 2>&1; then
    VAST_API_KEY="$key" vastai destroy instance "$id" --yes >>"$SETUPLOG" 2>&1
    rc=$?
  else
    curl -fsS -X DELETE \
      -H "Authorization: Bearer ${key}" \
      "https://console.vast.ai/api/v0/instances/${id}/" >>"$SETUPLOG" 2>&1
    rc=$?
  fi
  set -e
  echo "WATCHDOG_DESTROY_RC=$rc" | tee -a "$SETUPLOG"
  echo "destroyed_rc=$rc reason=$reason utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$MARKER"
}

setup_log_mtime() {
  if [[ -f "$SETUPLOG" ]]; then
    stat -c %Y "$SETUPLOG" 2>/dev/null || echo 0
  else
    echo 0
  fi
}

setup_log_size() {
  if [[ -f "$SETUPLOG" ]]; then
    wc -c < "$SETUPLOG" | tr -d ' \n' || echo 0
  else
    echo 0
  fi
}

started_at=$(date +%s)
silent_deadline=$((started_at + SILENT_FAIL_MIN * 60))
cap_deadline=$((started_at + SILENT_CAP_MIN * 60))
hard_deadline=$((started_at + MAX_MIN * 60))
last_mtime=$(setup_log_mtime)
last_size=$(setup_log_size)

while true; do
  now=$(date +%s)
  if [[ "$now" -ge "$hard_deadline" ]]; then
    if has_fail_marker || { [[ -f "$EXITFILE" ]] && [[ "$(tr -d ' \n\r' < "$EXITFILE")" != "0" ]]; }; then
      destroy_self "watchdog_max_wall_with_failure"
    else
      echo "WATCHDOG_EXIT max_wall without fail marker (leaving instance for local monitor)" | tee -a "$SETUPLOG"
    fi
    exit 0
  fi

  if training_healthy; then
    echo "WATCHDOG_EXIT training_healthy" | tee -a "$SETUPLOG"
    exit 0
  fi

  if has_fail_marker; then
    destroy_self "setup_or_smoke_failed_marker"
    exit 0
  fi

  # Early non-zero exit before SETUP_OK / FULL_TRAIN.
  if [[ -f "$EXITFILE" ]]; then
    rc="$(tr -d ' \n\r' < "$EXITFILE" || echo 1)"
    if [[ "$rc" != "0" ]] && ! grep -q 'FULL_TRAIN' "$SETUPLOG" 2>/dev/null; then
      destroy_self "early_exit_rc_${rc}"
      exit 0
    fi
  fi

  # Extend silent deadline while setup log is still advancing (long pip install).
  cur_mtime=$(setup_log_mtime)
  cur_size=$(setup_log_size)
  if [[ "$cur_mtime" != "$last_mtime" ]] || [[ "$cur_size" != "$last_size" ]]; then
    last_mtime=$cur_mtime
    last_size=$cur_size
    new_deadline=$((now + SILENT_FAIL_MIN * 60))
    if [[ "$new_deadline" -gt "$silent_deadline" ]]; then
      silent_deadline=$new_deadline
      echo "WATCHDOG_SILENT_EXTEND utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) deadline_epoch=$silent_deadline size=$cur_size" | tee -a "$SETUPLOG"
    fi
    if [[ "$silent_deadline" -gt "$cap_deadline" ]]; then
      silent_deadline=$cap_deadline
    fi
  fi

  # Silent hang: no SETUP_OK, log stale, past (extended) silent deadline, under cap.
  if [[ "$now" -ge "$silent_deadline" ]]; then
    log_age=$((now - cur_mtime))
    if [[ "$log_age" -ge "$SILENT_STALE_SEC" ]] \
      && ! grep -q 'SETUP_OK' "$SETUPLOG" 2>/dev/null \
      && ! training_healthy; then
      destroy_self "silent_setup_timeout_stale_${SILENT_STALE_SEC}s_cap_${SILENT_CAP_MIN}m"
      exit 0
    fi
  fi

  sleep "$POLL_SEC"
done
