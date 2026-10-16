#!/usr/bin/env bash
# Shared SETUP_FAILED gating for weighted SFT watchdog + monitor.
# Sourced by sft_setup_fail_watchdog.sh; copied to /workspace on sparse sync.
# Do not use script line-number thresholds — they drift when setup grows.
#
# Actionable SETUP_FAILED when:
#   1) marker carries reason= (nvidia-smi, trap, etc.), or
#   2) a SETUP_FAILED line appears *after* the last SETUP_PINS_OK /
#      SETUP_PHASE=pins_ok in the same file (not mere co-occurrence).
# Bare early SETUP_FAILED (legacy probe false positive, no reason=) is ignored.

actionable_setup_failed_in() {
  local f="$1"
  [[ -f "$f" ]] || return 1
  grep -q 'SETUP_FAILED' "$f" 2>/dev/null || return 1

  # Explicit reason= is always actionable (early nvidia-smi, trap, …).
  if grep -qE 'SETUP_FAILED[[:space:]]+line=[0-9]+[[:space:]]+reason=' "$f" 2>/dev/null; then
    return 0
  fi

  # Bare SETUP_FAILED only if it appears after the last pins-ok marker.
  local pins_line=0
  local i=0
  local line
  while IFS= read -r line || [[ -n "$line" ]]; do
    i=$((i + 1))
    case "$line" in
      *SETUP_PINS_OK*|*SETUP_PHASE=pins_ok*)
        pins_line=$i
        ;;
    esac
    if [[ "$pins_line" -gt 0 ]] && [[ "$i" -gt "$pins_line" ]] && [[ "$line" == *SETUP_FAILED* ]]; then
      return 0
    fi
  done < "$f"
  return 1
}
