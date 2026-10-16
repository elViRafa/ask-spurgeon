"""Tokenizer load contract for weighted SFT run 8 (no GPU)."""
from __future__ import annotations

import importlib
import os
import subprocess
import sys
import types
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "fine_tuning" / "scripts"
SETUP = SCRIPTS / "sft_remote_setup.sh"
CONSTRAINTS = SCRIPTS / "sft_gate0_sep6_constraints.txt"
TRAIN = SCRIPTS / "train_sft_sota.py"
UTILS = SCRIPTS / "sft_stop_token_utils.py"
REMOTE = SCRIPTS / "sft_remote_train_s8_weighted.sh"
SMOKE = SCRIPTS / "sft_tokenizer_cpu_smoke.py"
ORCH = SCRIPTS / "vast_sft_s8_weighted_orchestrate.ps1"


def test_sep6_pins_install_protobuf_and_sentencepiece() -> None:
    constraints = CONSTRAINTS.read_text(encoding="utf-8")
    setup = SETUP.read_text(encoding="utf-8")
    for pin in ("protobuf==7.36.1", "sentencepiece==0.2.2"):
        assert pin in constraints
        assert pin in setup
    pkgs = setup.split("local pkgs=(", 1)[1].split(")", 1)[0]
    assert "protobuf==7.36.1" in pkgs
    assert "sentencepiece==0.2.2" in pkgs


def test_loader_does_not_pass_fix_mistral_regex() -> None:
    utils = UTILS.read_text(encoding="utf-8")
    train = TRAIN.read_text(encoding="utf-8")
    assert "fix_mistral_regex=True" not in utils
    assert "fix_mistral_regex=True" not in train
    assert 'getattr(exc, "name", None) != "sft_stop_token_utils"' in train
    body = train.split("def load_dataprep_tokenizer", 1)[1].split("def _dataprep_tokenizer_source", 1)[0]
    assert "return load_qwen35_tokenizer(tok_source)" in body
    # The call sits outside the ImportError handler.
    assert body.index("except ImportError") < body.index("return load_qwen35_tokenizer")


def test_inner_import_error_is_not_swallowed() -> None:
    sys.path.insert(0, str(SCRIPTS))
    saved = sys.modules.get("sft_stop_token_utils")
    fake = types.ModuleType("sft_stop_token_utils")

    def load_qwen35_tokenizer(model, token=None):
        raise ImportError("requires the protobuf library")

    fake.load_qwen35_tokenizer = load_qwen35_tokenizer
    sys.modules["sft_stop_token_utils"] = fake
    try:
        train = importlib.import_module("train_sft_sota")
        with pytest.raises(ImportError, match="protobuf"):
            train.load_dataprep_tokenizer("unused-model")
    finally:
        if saved is None:
            sys.modules.pop("sft_stop_token_utils", None)
        else:
            sys.modules["sft_stop_token_utils"] = saved


def test_remote_runs_cpu_smoke_before_gpu_smoke_and_emits_setup_failed() -> None:
    text = REMOTE.read_text(encoding="utf-8")
    cpu = text.index("sft_tokenizer_cpu_smoke.py")
    gpu = text.index("run_smoke 1 4608")
    assert cpu < gpu
    fail_block = text.split("sft_tokenizer_cpu_smoke.py", 1)[1].split("mkdir -p /workspace/sft_s8_weighted/adapter", 1)[0]
    assert 'echo "SETUP_FAILED rc=1"' in fail_block
    assert 'echo "SMOKE_BEFORE_TRAIN_FAILED"' in text
    # Marker is its own line, copied to the smoke log the monitor also reads.
    assert 'echo "SMOKE_BEFORE_TRAIN_FAILED" | tee -a "$SETUPLOG" "$SMOKELOG"' in text


def test_orchestrator_copies_cpu_smoke_and_stops_on_fail_marker() -> None:
    text = ORCH.read_text(encoding="utf-8")
    assert "sft_tokenizer_cpu_smoke.py" in text
    assert "cp \"`$SRC/fine_tuning/scripts/sft_tokenizer_cpu_smoke.py\"" in text
    assert "$script:WeightedFailStop = $failReason" in text
    gate = text.split("if ($script:WeightedFailStop)", 1)[1]
    throw_at = gate.find('throw "Weighted adapter missing')
    exit_at = gate.find("exit 1")
    assert exit_at >= 0 and (throw_at < 0 or exit_at < throw_at)


def test_cpu_smoke_fails_when_tokenizer_dir_missing(tmp_path: Path) -> None:
    missing = tmp_path / "no-such-model"
    proc = subprocess.run(
        [sys.executable, str(SMOKE), "--base", str(missing), "--dataprep", str(missing)],
        capture_output=True,
        text=True,
        check=False,
    )
    combined = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "TOKENIZER_CPU_SMOKE_FAIL" in combined
    assert "tokenizer_config.json missing" in combined


def _local_tokenizer_dir() -> Path | None:
    env = (os.environ.get("SFT_TOKENIZER_SMOKE_MODEL") or "").strip()
    candidates = [Path(env)] if env else []
    candidates.append(
        REPO / "fine_tuning" / "kaggle" / "qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit"
    )
    for path in candidates:
        if path.is_dir() and (path / "tokenizer_config.json").is_file():
            return path
    return None


def test_cpu_smoke_on_local_model_when_present() -> None:
    model = _local_tokenizer_dir()
    if model is None:
        pytest.skip("local merged tokenizer files are not on this machine")
    proc = subprocess.run(
        [sys.executable, str(SMOKE), "--base", str(model), "--dataprep", str(model)],
        capture_output=True,
        text=True,
        check=False,
    )
    combined = proc.stdout + proc.stderr
    assert proc.returncode == 0, combined
    assert "TOKENIZER_CPU_SMOKE_OK" in combined
