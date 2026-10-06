#!/usr/bin/env python3
"""Wiring tests for S8 m_hi resume Isolation C. No GPU, no vastai, no Hub."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
CPT = SCRIPTS.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import vast_cpt_s8_mhi_resume_c_eval_readiness as ready  # noqa: E402

PS1 = (SCRIPTS / "vast_cpt_s8_mhi_resume_c_eval.ps1").read_text(encoding="utf-8")
PLAYBOOK = (CPT / "NEXT_CPT_S8_MHI_RESUME_C.md").read_text(encoding="utf-8")


def test_sha_pins_resume_and_refuses_phase_a() -> None:
    assert ready.sha_errors(ready.EXPECT_RESUME) == []
    phase_a_errors = ready.sha_errors(ready.PHASE_A)
    assert any("06354dfc" in err for err in phase_a_errors)
    assert any("mismatch" in err for err in phase_a_errors)
    assert ready.sha_errors("0" * 64)


def test_sha_refuses_s6_s7_adapters() -> None:
    for sha, label in ready.FORBIDDEN.items():
        errs = ready.sha_errors(sha)
        assert errs, label
        assert any(label.split()[0].lower() in err.lower() or sha[:8] in err for err in errs)


def test_wrong_local_bytes_are_not_ready() -> None:
    errors = ready.evaluate(
        adapter=SCRIPTS / "vast_cpt_s8_mhi_resume_c_eval_readiness.py",
        checkpoints=[],
        holdout_root=CPT / "kaggle" / "a_output_v6_p0" / "theology_holdouts",
        ps1_text=PS1,
    )
    assert any("SHA mismatch" in err or "resume SHA mismatch" in err for err in errors)
    assert any("checkpoint-2250" in err for err in errors)


def test_ps1_wiring_and_dry_head() -> None:
    assert ready.wiring_errors(PS1) == []
    assert ready.dry_head_errors(PS1) == []
    head, tail, errors = ready._dry_head_and_tail(PS1)
    assert errors == []
    assert "if (-not $Go)" in head
    assert head.strip().endswith("exit 0")
    code = ready._code_without_comments(head)
    assert "vastai" not in code
    assert "Show-VastAccountSummary" not in code
    assert "vast_provision" not in code
    assert "vast_cpt_s8_mhi_resume_c_eval_readiness.py" in head
    assert "vast_provision.ps1" in tail
    assert "vast_remote_stack_isolation_c.sh" in tail
    assert "vast_remote_c_eval.sh" not in tail
    assert '$ExpectedSha = "2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207"' in PS1
    assert '$ExpectedSha = "06354dfc' not in PS1
    assert "vast_cpt_s8_mhi_resume\\fetch\\mhi_resume\\theology_cpt_lora" in PS1.replace("/", "\\")
    assert "a_output_v6_p0" in PS1
    assert "vast_cpt_s8_mhi_resume_c" in PS1


def test_dry_head_rejects_rent_before_exit() -> None:
    rented = PS1.replace("if (-not $Go) {", "Show-VastAccountSummary\nif (-not $Go) {", 1)
    errs = ready.dry_head_errors(rented)
    assert any("Show-VastAccountSummary" in err for err in errs)


def test_playbook_dry_and_go_commands() -> None:
    assert ready.EXPECT_RESUME in PLAYBOOK
    assert "1.6349" in PLAYBOOK
    assert "1.701" in PLAYBOOK
    assert "1.670" in PLAYBOOK
    assert "a_output_v6_p0" in PLAYBOOK
    assert "vast_cpt_s8_mhi_resume_c" in PLAYBOOK
    assert "vast_remote_stack_isolation_c.sh" in PLAYBOOK
    assert "vast_remote_c_eval.sh" in PLAYBOOK
    assert ".\\vast_cpt_s8_mhi_resume_c_eval.ps1" in PLAYBOOK
    assert ".\\vast_cpt_s8_mhi_resume_c_eval.ps1 -Go" in PLAYBOOK
    assert "06354dfc" in PLAYBOOK
    # Dry command is the script with no -Go. The -Go line is a separate Forge command.
    dry_block = PLAYBOOK.split("## `-Go`", 1)[0]
    assert ".\\vast_cpt_s8_mhi_resume_c_eval.ps1 -Go" not in dry_block
    assert "Do not" in PLAYBOOK
