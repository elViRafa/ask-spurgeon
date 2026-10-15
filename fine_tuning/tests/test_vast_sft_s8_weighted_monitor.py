"""Contracts for weighted SFT Vast monitor harden (no GPU)."""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ORCH = REPO / "fine_tuning" / "scripts" / "vast_sft_s8_weighted_orchestrate.ps1"
REMOTE = REPO / "fine_tuning" / "scripts" / "sft_remote_train_s8_weighted.sh"


def parse_weighted_state(stdout: str, *, ssh_ok: bool = True) -> str:
    """Mirror of Get-WeightedTrainState parsing.

    SSH failure is always UNKNOWN — never treat as gone.
    SETUP_FAILED / SMOKE_BEFORE_TRAIN_FAILED break the monitor immediately.
    """
    if not ssh_ok:
        return "UNKNOWN"
    text = stdout or ""
    if "WEIGHTED_STATE=SMOKE_BEFORE_TRAIN_FAILED" in text:
        return "SMOKE_BEFORE_TRAIN_FAILED"
    if "WEIGHTED_STATE=SETUP_FAILED" in text:
        return "SETUP_FAILED"
    if "WEIGHTED_STATE=ALIVE" in text:
        return "ALIVE"
    if "WEIGHTED_STATE=DEAD" in text:
        return "DEAD"
    return "UNKNOWN"


def test_loading_timeout_default_is_twenty_minutes() -> None:
    text = ORCH.read_text(encoding="utf-8")
    assert "LoadingTimeoutMinutes = 20" in text
    assert "extends while sft_setup.log advances" in text
    assert "only until pidfile" in text.lower() or "only until the pidfile" in text.lower()


def test_save_weighted_evidence_before_both_destroy_paths() -> None:
    text = ORCH.read_text(encoding="utf-8")
    assert "function Save-WeightedEvidence" in text

    # Invoke-DestroyOnFail must call evidence before vast_destroy.
    destroy_fail = text.split("function Invoke-DestroyOnFail", 1)[1]
    destroy_fail_body = destroy_fail.split("function ", 1)[0]
    ev_pos = destroy_fail_body.find("Save-WeightedEvidence")
    des_pos = destroy_fail_body.find("vast_destroy.ps1")
    assert ev_pos >= 0, "Invoke-DestroyOnFail must call Save-WeightedEvidence"
    assert des_pos >= 0, "Invoke-DestroyOnFail must call vast_destroy"
    assert ev_pos < des_pos, "evidence must come before destroy on fail path"

    # Post-fetch destroy path.
    post = text.split("Destroying instance after fetch", 1)[1]
    post_body = post.split("if (-not $adapterOk)", 1)[0]
    ev_pos2 = post_body.find("Save-WeightedEvidence")
    des_pos2 = post_body.find("vast_destroy.ps1")
    assert ev_pos2 >= 0, "post-fetch path must call Save-WeightedEvidence"
    assert des_pos2 >= 0, "post-fetch path must call vast_destroy"
    assert ev_pos2 < des_pos2, "evidence must come before destroy on post-fetch path"


def test_state_parser_canned_outputs() -> None:
    alive = """
SETUP_MTIME=1710000000
SETUP_SIZE=4096
PIDFILE=1
WEIGHTED_STATE=ALIVE
"""
    dead = """
SETUP_MTIME=1710000000
SETUP_SIZE=4096
PIDFILE=1
WEIGHTED_STATE=DEAD
"""
    unknown_no_pid = """
SETUP_MTIME=0
SETUP_SIZE=0
PIDFILE=0
WEIGHTED_STATE=UNKNOWN
"""
    setup_failed = """
SETUP_MTIME=1710000000
SETUP_SIZE=1200
PIDFILE=0
FAIL_MARKER=SETUP_FAILED
WEIGHTED_STATE=SETUP_FAILED
"""
    smoke_failed = """
SETUP_MTIME=1710000000
SETUP_SIZE=2200
PIDFILE=1
FAIL_MARKER=SMOKE_BEFORE_TRAIN_FAILED
WEIGHTED_STATE=SMOKE_BEFORE_TRAIN_FAILED
"""
    ambiguous = "connection timed out"
    assert parse_weighted_state(alive) == "ALIVE"
    assert parse_weighted_state(dead) == "DEAD"
    assert parse_weighted_state(unknown_no_pid) == "UNKNOWN"
    assert parse_weighted_state(setup_failed) == "SETUP_FAILED"
    assert parse_weighted_state(smoke_failed) == "SMOKE_BEFORE_TRAIN_FAILED"
    assert parse_weighted_state(ambiguous) == "UNKNOWN"
    assert parse_weighted_state(alive, ssh_ok=False) == "UNKNOWN"
    assert parse_weighted_state(dead, ssh_ok=False) == "UNKNOWN"
    assert parse_weighted_state(setup_failed, ssh_ok=False) == "UNKNOWN"


def test_orchestrator_has_alive_dead_unknown_and_debounce() -> None:
    text = ORCH.read_text(encoding="utf-8")
    assert "function Get-WeightedTrainState" in text
    assert "WEIGHTED_STATE=ALIVE" in text
    assert "WEIGHTED_STATE=DEAD" in text
    assert "WEIGHTED_STATE=UNKNOWN" in text
    assert "WEIGHTED_STATE=SETUP_FAILED" in text
    assert "WEIGHTED_STATE=SMOKE_BEFORE_TRAIN_FAILED" in text
    assert "deadNeeded = 3" in text
    assert "unknownDestroyMinutes = 10" in text
    assert "Test-VastInstanceStillPresent" in text
    assert "show\", \"instance\"" in text or 'show", "instance"' in text
    # Boolean pgrep-only helper must be gone.
    assert "function Test-WeightedTrainRunning" not in text
    # SETUP_FAILED gated until pins OK / reason= / line past pin install.
    assert "SETUP_PINS_OK" in text
    assert "actionable_setup_failed" in text
    # Fail-fast: evidence then break before waiting out loading timeout.
    assert "SETUP_FAILED" in text
    assert "SMOKE_BEFORE_TRAIN_FAILED" in text
    fail_fast = text.split("Break fast on setup/smoke", 1)
    assert len(fail_fast) == 2
    assert "Save-WeightedEvidence" in fail_fast[1].split("if ($st.State -eq \"ALIVE\")", 1)[0]


def test_remote_train_writes_pid_exit_and_waits() -> None:
    text = REMOTE.read_text(encoding="utf-8")
    assert "sft_train.pid" in text
    assert "sft_train.exit" in text
    assert "sft_setup.log" in text
    assert "tee -a" in text
    assert "wait \"$TRAIN_PID\"" in text or 'wait "$TRAIN_PID"' in text
    assert 'pgrep -f "[t]rain_sft_sota.py"' in text
    # Must not detach-and-exit without wait (old false-destroy pattern).
    assert "nohup python3 -u /workspace/train_sft_sota.py" not in text


def test_orchestrator_and_remote_are_lf_only() -> None:
    assert b"\r" not in ORCH.read_bytes()
    assert b"\r" not in REMOTE.read_bytes()
