#!/usr/bin/env python3
"""Unit tests for S6 monitor completion gates (no SSH)."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import s6_monitor_until_done as mon  # noqa: E402


def test_ssh_flake_never_finished() -> None:
    log = "Saved run config\n"
    assert mon.training_finished(log, running=None) is False


def test_still_running_never_finished() -> None:
    log = "Saved run config\n"
    assert mon.training_finished(log, running=True) is False


def test_not_running_without_marker_not_finished() -> None:
    log = "{'loss': '1.9', 'epoch': '0.5'}\n  51%|     | 2110/4128 ["
    assert mon.log_has_done_marker(log) is False
    assert mon.training_finished(log, running=False) is False


def test_not_running_with_saved_run_config() -> None:
    log = "Saved run config to /workspace/theology_cpt_run_config.json\n"
    assert mon.training_finished(log, running=False) is True


def test_not_running_with_composite_stop() -> None:
    log = "COMPOSITE EARLY-STOP @ step 3200: metrics=['eval_spurgeon_loss', 'eval_mix_loss']\n"
    assert mon.training_finished(log, running=False) is True


def test_not_running_with_full_epoch() -> None:
    log = "100%|██████████| 4128/4128 [12:00:00<00:00, 10s/it]\n"
    assert mon.training_finished(log, running=False) is True


def test_empty_log_not_finished() -> None:
    assert mon.training_finished("", running=False) is False
    assert mon.training_finished("", running=None) is False


def main() -> None:
    test_ssh_flake_never_finished()
    test_still_running_never_finished()
    test_not_running_without_marker_not_finished()
    test_not_running_with_saved_run_config()
    test_not_running_with_composite_stop()
    test_not_running_with_full_epoch()
    test_empty_log_not_finished()
    print("PASS: ssh flake never finished")
    print("PASS: running never finished")
    print("PASS: no marker not finished")
    print("PASS: Saved run config")
    print("PASS: COMPOSITE EARLY-STOP")
    print("PASS: 4128/4128")
    print("PASS: empty log")


if __name__ == "__main__":
    main()
