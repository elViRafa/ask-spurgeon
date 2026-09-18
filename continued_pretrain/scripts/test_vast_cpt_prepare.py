#!/usr/bin/env python3
"""Sanity tests for Vast CPT prepare scripts (no GPU, no rent)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import s6_monitor_until_done as mon  # noqa: E402
import vast_cpt_monitor_until_done as vmon  # noqa: E402


def test_remote_uses_conda_python() -> None:
    sh = (SCRIPTS / "vast_cpt_remote_continue_b.sh").read_text(encoding="utf-8")
    assert "ENV_NAME=unsloth_cpt" in sh
    assert 'nohup "$PY" -u /workspace/train_cpt_sota.py' in sh
    assert "python3 -u /workspace/train_cpt_sota.py" not in sh
    assert "train_cpt_sota.py --install" not in sh
    assert "checkpoint-2050" in sh
    assert "S6_FRESH_START" in sh
    assert "nvidia/cuda" not in sh  # image is provision-side


def test_monitor_reuses_s6_gates() -> None:
    log = "Saved run config to /workspace/theology_cpt_run_config.json\n"
    assert vmon.mon.training_finished(log, running=False) is True
    assert mon.training_finished(log, running=None) is False


def test_scripts_exist() -> None:
    for name in (
        "vast_cpt_common.ps1",
        "vast_cpt_search.ps1",
        "vast_cpt_orchestrate.ps1",
        "vast_cpt_sync.ps1",
        "vast_cpt_launch.ps1",
        "vast_cpt_fetch.ps1",
        "vast_cpt_pack_payload.ps1",
        "vast_cpt_local_readiness.py",
        "vast_cpt_monitor_until_done.py",
    ):
        assert (SCRIPTS / name).is_file(), name


def main() -> None:
    test_remote_uses_conda_python()
    test_monitor_reuses_s6_gates()
    test_scripts_exist()
    print("PASS: conda remote launcher")
    print("PASS: monitor gates")
    print("PASS: script files exist")


if __name__ == "__main__":
    main()
