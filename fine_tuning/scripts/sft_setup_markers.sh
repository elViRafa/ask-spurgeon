#!/usr/bin/env bash
# Shared fail-marker gating for weighted SFT watchdog + pc1 monitor.
# Sourced by sft_setup_fail_watchdog.sh; copied to /workspace on sparse sync.
#
# Match anchored lines only. A mention inside another log line is not a fail.
#   ^SETUP_FAILED rc=<digits>
#   ^SMOKE_BEFORE_TRAIN_FAILED
# SETUP_TRAP_INFO (ERR trap noise, including || true and set +e) is never actionable.
# Do not use script line numbers or reason=trap — both false-destroyed live GPUs.

actionable_setup_failed_in() {
  local f="$1"
  [[ -f "$f" ]] || return 1
  grep -qE '^SETUP_FAILED rc=[0-9]+([[:space:]]|$)' "$f" 2>/dev/null
}

actionable_smoke_failed_in() {
  local f="$1"
  [[ -f "$f" ]] || return 1
  grep -qE '^SMOKE_BEFORE_TRAIN_FAILED([[:space:]]|$)' "$f" 2>/dev/null
}

first_trigger_line_in() {
  local f="$1"
  local line=""
  [[ -f "$f" ]] || return 1
  # head closes the pipe early; avoid pipefail SIGPIPE hiding a real match.
  line="$(grep -E '^(SETUP_FAILED rc=[0-9]+|SMOKE_BEFORE_TRAIN_FAILED)([[:space:]]|$)' "$f" 2>/dev/null | head -n 1 || true)"
  [[ -n "$line" ]] || return 1
  printf '%s\n' "$line"
}
