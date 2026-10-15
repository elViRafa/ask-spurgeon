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
POLL_SEC="${SFT_WATCHDOG_POLL_SEC:-20}"
MAX_MIN="${SFT_WATCHDOG_MAX_MIN:-45}"
# Grace before treating silent failure (no SETUP_OK) as billable idle.
SILENT_FAIL_MIN="${SFT_WATCHDOG_SILENT_FAIL_MIN:-25}"

mkdir -p /workspace
echo "WATCHDOG_START utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) poll=${POLL_SEC}s max=${MAX_MIN}m" | tee -a "$SETUPLOG"

if [[ -f "$WATCH_ENV" ]]; then
  # shellcheck disable=SC1090
  source "$WATCH_ENV"
fi

# SETUP_FAILED is actionable when pins already succeeded, when the marker carries an
# explicit reason= (early nvidia-smi etc.), or when the trap line is past pin install.
# Bare early SETUP_FAILED (pre-torch probe false positive) must not destroy.
actionable_setup_failed_in() {
  local f="$1"
  [[ -f "$f" ]] || return 1
  grep -q 'SETUP_FAILED' "$f" 2>/dev/null || return 1
  if grep -q 'SETUP_PINS_OK' "$f" 2>/dev/null; then
    return 0
  fi
  if grep -qE 'SETUP_FAILED line=[0-9]+ reason=' "$f" 2>/dev/null; then
    return 0
  fi
  # Trap line past pin-install region (assert_pins / SETUP_PINS_OK zone starts ~470+).
  local line
  while IFS= read -r line; do
    if [[ "$line" =~ SETUP_FAILED\ line=([0-9]+) ]]; then
      if [[ "${BASH_REMATCH[1]}" -ge 470 ]]; then
        return 0
      fi
    fi
  done < <(grep -E 'SETUP_FAILED line=[0-9]+' "$f" 2>/dev/null || true)
  return 1
}

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

started_at=$(date +%s)
silent_deadline=$((started_at + SILENT_FAIL_MIN * 60))
hard_deadline=$((started_at + MAX_MIN * 60))

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

  # Silent hang: no SETUP_OK after grace and no advancing train.
  if [[ "$now" -ge "$silent_deadline" ]]; then
    if ! grep -q 'SETUP_OK' "$SETUPLOG" 2>/dev/null && ! training_healthy; then
      destroy_self "silent_setup_timeout_${SILENT_FAIL_MIN}m"
      exit 0
    fi
  fi

  sleep "$POLL_SEC"
done
