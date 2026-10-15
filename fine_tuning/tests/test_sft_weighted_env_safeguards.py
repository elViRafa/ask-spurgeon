"""Contracts for weighted SFT env isolation, pins, smoke, and evidence (no GPU)."""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "fine_tuning" / "scripts"
SETUP = SCRIPTS / "sft_remote_setup.sh"
REMOTE = SCRIPTS / "sft_remote_train_s8_weighted.sh"
ORCH = SCRIPTS / "vast_sft_s8_weighted_orchestrate.ps1"
CONSTRAINTS = SCRIPTS / "sft_gate0_sep6_constraints.txt"
TRAIN = SCRIPTS / "train_sft_sota.py"
MASK_TEST = REPO / "fine_tuning" / "tests" / "test_sft_s3_mask_all_rows.py"


def test_constraints_file_has_sep6_pins() -> None:
    text = CONSTRAINTS.read_text(encoding="utf-8")
    for pin in (
        "torch==2.11.0+cu126",
        "transformers==5.5.0",
        "peft==0.20.0",
        "trl==0.24.0",
        "accelerate==1.14.0",
        "bitsandbytes==0.50.2",
        "triton==3.6.0",
        "unsloth_zoo==2026.9.1",
    ):
        assert pin in text, f"missing pin {pin}"
    # Pins only — no FLA / causal-conv requirement lines.
    pin_lines = [ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    joined = "\n".join(pin_lines)
    assert "flash-linear-attention" not in joined
    assert "causal-conv1d" not in joined
    assert "flash_linear_attention" not in joined


def test_setup_uses_isolated_venv_or_conda_and_unsets_ld_library_path() -> None:
    text = SETUP.read_text(encoding="utf-8")
    assert "unset LD_LIBRARY_PATH" in text
    assert "sft_venv" in text
    assert "miniforge" in text.lower() or "Miniforge" in text
    assert "python3.11 -m venv" in text or "python3.11 -m venv --clear" in text
    assert "--system-site-packages" not in text
    assert "break-system-packages" not in text
    assert "sft_gate0_sep6_constraints.txt" in text
    assert "sft_pip_freeze.txt" in text
    assert "PIN_ASSERT_OK" in text
    assert "6816025b" in text
    assert "flash_linear_attention" in text  # refuse check
    assert "causal_conv1d" in text
    assert "PYTHONFAULTHANDLER=1" in text
    assert "cpython-310" in text


def test_remote_train_faulthandler_smoke_before_train_expandable_toggle() -> None:
    text = REMOTE.read_text(encoding="utf-8")
    assert "unset LD_LIBRARY_PATH" in text
    assert "PYTHONFAULTHANDLER=1" in text
    assert "-X faulthandler" in text
    assert "SMOKE_BEFORE_TRAIN" in text
    assert "CUDA_LAUNCH_BLOCKING=1" in text
    assert "run_smoke" in text
    assert "expand_on_seq4608" in text
    assert "expand_off_seq4608" in text
    assert "expand_off_seq2048" in text
    assert "SFT_EXPANDABLE_SEGMENTS" in text
    assert "apply_expandable" in text
    # Smoke must complete before full train starts.
    smoke_pos = text.index("SMOKE_BEFORE_TRAIN")
    full_pos = text.index("FULL_TRAIN")
    assert smoke_pos < full_pos
    train_bg = text.index('train_sft_sota.py > /workspace/sft_train.log')
    assert full_pos < train_bg
    # CUDA_LAUNCH_BLOCKING only in smoke path — unset before full train.
    assert "unset CUDA_LAUNCH_BLOCKING" in text
    assert "sft_smoke_fail" in text
    assert "SMOKE_BEFORE_TRAIN_FAILED" in text


def test_train_script_expandable_toggle_and_smoke_flag() -> None:
    text = TRAIN.read_text(encoding="utf-8")
    assert "_apply_expandable_segments_env" in text
    assert "SFT_EXPANDABLE_SEGMENTS" in text
    assert "_smoke_enabled" in text
    assert "_select_longest_text_rows" in text
    assert 'add_argument(\n        "--smoke"' in text or '"--smoke"' in text
    assert "SFT_SMOKE_PASS" in text
    assert "SFT_MAX_STEPS" in text


def test_evidence_asserts_files_status_listing_scp_fallback() -> None:
    text = ORCH.read_text(encoding="utf-8")
    assert "function Save-WeightedEvidence" in text
    body = text.split("function Save-WeightedEvidence", 1)[1]
    body = body.split("function Invoke-DestroyOnFail", 1)[0]
    assert "status.txt" in body
    assert "listing.txt" in body
    assert "scp_" in body or "scp fallback" in body.lower() or "SCP fallback" in body
    assert "ASSERT FAIL" in body
    assert "evidence_ok=" in body
    assert "payload_ok" in body
    # Evidence before destroy on both paths.
    destroy_fail = text.split("function Invoke-DestroyOnFail", 1)[1]
    destroy_fail_body = destroy_fail.split("function ", 1)[0]
    assert destroy_fail_body.find("Save-WeightedEvidence") < destroy_fail_body.find(
        "vast_destroy.ps1"
    )


def test_evidence_before_destroy_contract() -> None:
    text = ORCH.read_text(encoding="utf-8")
    post = text.split("Destroying instance after fetch", 1)[1]
    post_body = post.split("if (-not $adapterOk)", 1)[0]
    assert post_body.find("Save-WeightedEvidence") < post_body.find("vast_destroy.ps1")


def test_mask_test_uses_dynamic_row_count() -> None:
    text = MASK_TEST.read_text(encoding="utf-8")
    assert "EXPECTED_MIX_ROWS" not in text
    assert "len(rag_rows) + len(theo_rows)" in text
    assert "expected_mix_rows" in text


def test_constraints_synced_in_orchestrator() -> None:
    text = ORCH.read_text(encoding="utf-8")
    assert "sft_gate0_sep6_constraints.txt" in text
    assert "sft_smoke.log" in text
    assert "sft_pip_freeze.txt" in text


def test_shell_scripts_are_lf_only() -> None:
    for path in (SETUP, REMOTE, CONSTRAINTS):
        assert b"\r" not in path.read_bytes(), f"{path.name} must be LF-only"
    assert b"\r" not in ORCH.read_bytes()
