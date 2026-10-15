"""Contracts for weighted SFT env isolation, pins, smoke, and evidence (no GPU)."""
from __future__ import annotations

import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "fine_tuning" / "scripts"
SETUP = SCRIPTS / "sft_remote_setup.sh"
WATCHDOG = SCRIPTS / "sft_setup_fail_watchdog.sh"
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


def test_setup_skips_unsloth_unless_backend_unsloth() -> None:
    text = SETUP.read_text(encoding="utf-8")
    assert "SFT_BACKEND=" in text
    assert '== "unsloth"' in text
    assert "skipping unsloth install" in text
    assert "skipping unsloth_zoo install" in text
    assert_pins = text.split("assert_pins()", 1)[1].split("write_env_hooks", 1)[0]
    assert 'backend == "unsloth"' in assert_pins
    assert "unsloth: skipped" in assert_pins
    assert "unsloth skipped" in text
    # Every top-level `import unsloth` must sit under an unsloth backend gate.
    for m in re.finditer(r"(?m)^import unsloth\b", text):
        gate = text[max(0, m.start() - 500) : m.start()]
        assert '== "unsloth"' in gate or "backend == \"unsloth\"" in gate


def test_setup_uses_isolated_venv_or_conda_and_unsets_ld_library_path() -> None:
    text = SETUP.read_text(encoding="utf-8")
    assert "unset LD_LIBRARY_PATH" in text
    assert "sft_venv" in text
    assert "miniforge" in text.lower() or "Miniforge" in text
    assert "python3.11 -m venv" in text or "python3.11 -m venv --clear" in text
    # Must never enable system site-packages (comment may mention the flag).
    assert re.search(r"(?m)^\s*python3\.11 -m venv[^\n]*--system-site-packages", text) is None
    assert "break-system-packages" not in text
    assert "include-system-site-packages = false" in text
    assert "never pass --system-site-packages" in text
    assert "SYS_PATH_ISOLATED_OK" in text or "no image dist-packages" in text
    assert "dist-packages" in text
    assert "PYTHONNOUSERSITE=1" in text
    assert "unset PYTHONPATH" in text
    assert "sft_gate0_sep6_constraints.txt" in text
    assert "sft_pip_freeze.txt" in text
    assert "PIN_ASSERT_OK" in text
    assert "6816025b" in text
    assert "flash_linear_attention" in text  # refuse check
    assert "causal_conv1d" in text
    assert "PYTHONFAULTHANDLER=1" in text
    assert "cpython-310" in text


def test_setup_prints_ld_and_cuda_before_first_unset() -> None:
    text = SETUP.read_text(encoding="utf-8")
    first_unset = text.index("unset LD_LIBRARY_PATH")
    preamble = text[:first_unset]
    assert "LD_LIBRARY_PATH=" in preamble
    assert "ldconfig" in preamble
    assert "libcuda" in preamble
    assert "torch.cuda.is_available()" in preamble
    assert "nvidia-smi" in preamble
    assert "SETUP_FAILED" in text


def test_setup_err_trap_writes_setup_failed_marker() -> None:
    text = SETUP.read_text(encoding="utf-8")
    assert "SETUP_FAILED line=" in text
    assert "trap" in text
    assert "on_setup_err" in text or "SETUP_FAILED line=${" in text
    assert "SETUP_PINS_OK" in text
    assert "PRE_TORCH_PROBE_BEGIN" in text
    assert "trap - ERR" in text
    assert "PRE_UNSET_TORCH_IMPORT_SKIP" in text


def test_watchdog_gates_setup_failed_on_pins_ok() -> None:
    text = WATCHDOG.read_text(encoding="utf-8")
    assert "SETUP_PINS_OK" in text
    assert "actionable_setup_failed" in text
    assert "reason=" in text


def test_setup_pip_not_quiet() -> None:
    text = SETUP.read_text(encoding="utf-8")
    # No quiet pip installs (operator needs full log on Vast).
    assert "pip install -q" not in text
    assert "pip install --upgrade pip" in text
    assert "verbose; no -q" in text or "no -q" in text


def test_watchdog_self_destroys_after_evidence() -> None:
    text = WATCHDOG.read_text(encoding="utf-8")
    assert "SETUP_FAILED" in text
    assert "SMOKE_BEFORE_TRAIN_FAILED" in text
    assert "sft_fail_evidence" in text
    assert "write_evidence" in text or "WATCHDOG_EVIDENCE_OK" in text
    assert "destroy" in text.lower()
    assert "VAST_INSTANCE_ID" in text
    assert "VAST_API_KEY" in text
    assert "console.vast.ai/api/v0/instances" in text
    # Evidence before destroy.
    ev = text.index("WATCHDOG_EVIDENCE_OK") if "WATCHDOG_EVIDENCE_OK" in text else text.index("write_evidence")
    dest = text.index("WATCHDOG_DESTROY_BEGIN")
    assert ev < dest


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
    # Do not shorten the primary seq length contract.
    assert "SFT_MAX_SEQ_LENGTH=4608" in text


def test_train_script_expandable_toggle_and_smoke_flag() -> None:
    text = TRAIN.read_text(encoding="utf-8")
    assert "_apply_expandable_segments_env" in text
    assert "SFT_EXPANDABLE_SEGMENTS" in text
    assert "_smoke_enabled" in text
    assert "_select_longest_text_rows" in text
    assert 'add_argument(\n        "--smoke"' in text or '"--smoke"' in text
    assert "SFT_SMOKE_PASS" in text
    assert "SFT_MAX_STEPS" in text
    # Unsloth import only in unsloth train path.
    unsloth_fn = text.split("def _train_unsloth", 1)[1].split("\ndef ", 1)[0]
    assert "from unsloth import" in unsloth_fn
    peft_fn = text.split("def _train_peft", 1)[1].split("def _train_unsloth", 1)[0]
    assert "from unsloth import" not in peft_fn
    assert "import unsloth" not in peft_fn


def test_orchestrator_go_implies_monitor_transcript_try_catch_watchdog() -> None:
    text = ORCH.read_text(encoding="utf-8")
    assert "GO_IMPLIES_START_MONITOR" in text or "forcing StartMonitor" in text
    assert "Start-Transcript" in text
    assert "Stop-Transcript" in text
    assert "sft_setup_fail_watchdog.sh" in text
    assert "WATCHDOG_ENV_OK" in text or "sft_watchdog_env" in text
    assert "weighted launch failed" in text
    assert "try {" in text
    assert "Invoke-DestroyOnFail" in text
    # Fail-fast monitor markers.
    assert "SETUP_FAILED" in text
    assert "SMOKE_BEFORE_TRAIN_FAILED" in text
    assert "evidence then destroy" in text.lower() or "WEIGHTED_STATE={1}" in text


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
    assert "evidence saved (incomplete)" not in body
    assert 'Write-Host "evidence saved: $evDir"' in body
    assert "nothing real copied" in body or "INCOMPLETE" in body
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
    assert "sft_setup_fail_watchdog.sh" in text


def test_shell_scripts_are_lf_only() -> None:
    for path in (SETUP, REMOTE, WATCHDOG, CONSTRAINTS):
        assert b"\r" not in path.read_bytes(), f"{path.name} must be LF-only"
    assert b"\r" not in ORCH.read_bytes()


def test_optional_cpu_import_smoke() -> None:
    """Optional: import peft-path stack on CPU when RUN_SLOW_IMPORT_SMOKE=1."""
    if os.environ.get("RUN_SLOW_IMPORT_SMOKE") != "1":
        return
    import importlib

    for mod in ("torch", "transformers", "peft", "trl", "accelerate", "bitsandbytes"):
        importlib.import_module(mod)
    # Must not require unsloth on peft path.
    try:
        importlib.import_module("unsloth")
    except ImportError:
        pass
