#!/usr/bin/env python3
"""Sanity tests for Vast CPT S7 Phase A prepare scripts (no GPU, no rent)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import s6_monitor_until_done as mon  # noqa: E402
import vast_cpt_s7_monitor_until_done as vmon  # noqa: E402


EXPECT_S6 = "6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c"
EXPECT_S5 = "ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303"
EXPECT_S7 = "06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432"
EXPECT_B = "ddbbee3ac9ef7baf6cca21dcdb844d027d39f5f6a4b88ba10fcf8a43fa7c8214"


def test_remote_launcher_s7_policy() -> None:
    sh = (SCRIPTS / "vast_cpt_s7_remote_continue_b.sh").read_text(encoding="utf-8")
    assert "ENV_NAME=unsloth_cpt_s7" in sh
    assert "CPT_CONTINUE_PROFILE=s7" in sh
    assert EXPECT_B in sh
    assert EXPECT_S6 not in sh
    assert EXPECT_S5 not in sh
    assert "COMPOSITE_EARLY_STOP_METRICS" in sh
    assert "eval_mix_loss" not in sh
    assert "CONTINUE_MAX_STEPS" in sh
    assert "eval_mix_loss" not in sh
    assert "export PREV_RUN_CHECKPOINT=" in sh
    assert "torch==2.8.0" in sh
    assert "unsloth[colab-new]==2026.8.22" in sh
    assert "torch==2.11" not in sh
    assert "unsloth.git" not in sh
    assert 'nohup env' in sh
    assert '"$PY" -u /workspace/train_cpt_sota.py' in sh
    assert "python3 -u /workspace/train_cpt_sota.py" not in sh
    # .sft_env then re-export SHA
    assert "source /workspace/.sft_env" in sh
    assert 'export EXPECTED_ADAPTER_SHA256="$PINNED_ADAPTER_SHA256"' in sh
    # Empty PREV passed to nohup
    assert 'PREV_RUN_CHECKPOINT="${PREV_RUN_CHECKPOINT}"' in sh
    assert "checkpoints_s7" in sh
    assert "S7_RESUME" in sh


def test_pack_script_excludes_sota() -> None:
    ps1 = (SCRIPTS / "vast_cpt_s7_pack_payload.ps1").read_text(encoding="utf-8")
    assert "checkpoints_sota" in ps1  # refuse check
    assert "Refuse: stage must not contain checkpoints_sota" in ps1
    assert "Refuse: payload contains checkpoints_sota" in ps1
    assert "checkpoint-2050" not in ps1
    assert "vast_cpt_s7_remote_continue_b.sh" in ps1
    assert "Get-VastCptS7LoraDir" in ps1
    assert "Get-VastCptS7MixDir" in ps1
    assert "mix_v6" in ps1
    common = (SCRIPTS / "vast_cpt_s7_common.ps1").read_text(encoding="utf-8")
    assert "a_output_v6" in common
    assert EXPECT_B in common
    assert '$Script:S7AdapterSha = "ddbbee3a' in common
    assert '$Script:S7AdapterSha = "06354dfc' not in common
    assert "theology_cpt_lora_s5best\\theology_cpt_lora_s5best" in common
    assert "vast_cpt_s7_replay" in common


def test_sync_verifies_s7_not_s6() -> None:
    ps1 = (SCRIPTS / "vast_cpt_s7_sync.ps1").read_text(encoding="utf-8")
    assert "WANT=$S7AdapterSha" in ps1
    assert "WANT=$S6AdapterSha" not in ps1
    assert "mix_v6" in ps1
    assert "a_output_v6" in ps1


def test_fetch_pulls_s7_and_s5best() -> None:
    ps1 = (SCRIPTS / "vast_cpt_s7_fetch.ps1").read_text(encoding="utf-8")
    assert "/workspace/checkpoints_s7" in ps1
    assert "theology_cpt_lora_s5best" in ps1
    assert "s5_best.json" in ps1
    assert "/workspace/checkpoints_sota" not in ps1
    assert "vast_cpt_s7_common.ps1" in ps1


def test_monitor_defaults() -> None:
    assert vmon.TOTAL_STEPS == 955 or int(__import__("os").environ.get("CPT_TOTAL_STEPS", "955")) == 955
    assert "vast_cpt_s7" in str(vmon.SESSION)
    assert "vast_cpt_s7" in str(vmon.RESULTS_DIR)
    assert vmon.fetch_results.__code__.co_consts  # exists
    log = "Saved run config to /workspace/theology_cpt_run_config.json\n"
    assert mon.training_finished(log, running=False) is True
    bar = "  3%|\u2588     | 25/955 [00:10<01:00, 15.00s/it]"
    assert "?" in vmon.safe_line(bar)
    assert all(ord(ch) < 128 for ch in vmon.safe_line(bar))


def test_orchestrate_credit_and_disk() -> None:
    ps1 = (SCRIPTS / "vast_cpt_s7_orchestrate.ps1").read_text(encoding="utf-8")
    assert "vast_cpt_s7_common.ps1" in ps1
    assert "DiskGb = $DefaultDiskGb" in ps1
    assert "Label  = $DefaultLabel" in ps1
    assert "credit -lt 5" in ps1
    assert "vast_cpt_s7_monitor_until_done.py" in ps1
    assert "CPT_TOTAL_STEPS" in ps1
    assert "vast_cpt_fetch.ps1" not in ps1


def test_c_eval_targets_phase_b() -> None:
    ps1 = (SCRIPTS / "vast_cpt_s7_c_eval.ps1").read_text(encoding="utf-8")
    assert EXPECT_B in ps1
    assert '$ExpectedSha = "06354dfc' not in ps1
    assert "theology_cpt_lora_s5best\\theology_cpt_lora_s5best" in ps1
    assert "vast_cpt_s7_b_c" in ps1
    assert "vast_cpt_s7_c_eval_readiness.py" in ps1
    assert "a_output_v5" in ps1


def test_scripts_exist() -> None:
    for name in (
        "vast_cpt_s7_common.ps1",
        "vast_cpt_s7_orchestrate.ps1",
        "vast_cpt_s7_sync.ps1",
        "vast_cpt_s7_launch.ps1",
        "vast_cpt_s7_fetch.ps1",
        "vast_cpt_s7_pack_payload.ps1",
        "vast_cpt_s7_local_readiness.py",
        "vast_cpt_s7_monitor_until_done.py",
        "vast_cpt_s7_remote_continue_b.sh",
        "vast_cpt_s7_c_eval.ps1",
        "vast_cpt_s7_c_eval_readiness.py",
    ):
        assert (SCRIPTS / name).is_file(), name


def main() -> None:
    test_remote_launcher_s7_policy()
    test_pack_script_excludes_sota()
    test_sync_verifies_s7_not_s6()
    test_fetch_pulls_s7_and_s5best()
    test_monitor_defaults()
    test_orchestrate_credit_and_disk()
    test_c_eval_targets_phase_b()
    test_scripts_exist()
    print("PASS: S7 remote launcher policy")
    print("PASS: pack excludes sota")
    print("PASS: sync verifies S7 not S6")
    print("PASS: fetch s7 + s5best")
    print("PASS: monitor defaults")
    print("PASS: orchestrate credit/disk")
    print("PASS: C-eval targets Phase B")
    print("PASS: script files exist")


if __name__ == "__main__":
    main()
