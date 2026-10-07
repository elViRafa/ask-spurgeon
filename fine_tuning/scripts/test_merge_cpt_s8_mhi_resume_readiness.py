#!/usr/bin/env python3
"""Wiring tests for S8 m_hi resume merge export. No GPU."""
from __future__ import annotations

from pathlib import Path

import cpt_s8_mhi_resume_merge_readiness as ready
import merge_cpt_s8_mhi_resume as merge

REPO = Path(__file__).resolve().parents[2]
EXPORT_MD = REPO / "continued_pretrain/NEXT_CPT_S8_MHI_RESUME_HF_EXPORT.md"
MERGE_PY = REPO / "fine_tuning/scripts/merge_cpt_s8_mhi_resume.py"
UPLOAD_PY = REPO / "fine_tuning/scripts/upload_cpt_s8_mhi_resume_merged_hf.py"
REMOTE_SH = REPO / "fine_tuning/scripts/cpt_remote_merge_s8_mhi_resume.sh"
ORCH_PS1 = REPO / "continued_pretrain/scripts/vast_cpt_s8_mhi_resume_hf_export_orchestrate.ps1"
READY_PY = REPO / "fine_tuning/scripts/cpt_s8_mhi_resume_merge_readiness.py"


def test_default_paths_ready_when_weights_present() -> None:
    parent = ready.DEFAULT_PARENT
    resume = ready.DEFAULT_RESUME
    if not (parent / "adapter_model.safetensors").is_file():
        return
    if not (resume / "adapter_model.safetensors").is_file():
        return
    assert ready.evaluate_merge_paths(parent, resume) == []


def test_export_runbook_and_scripts_exist() -> None:
    assert MERGE_PY.is_file()
    assert UPLOAD_PY.is_file()
    assert EXPORT_MD.is_file()
    text = EXPORT_MD.read_text(encoding="utf-8")
    assert "2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207" in text
    assert "merge_cpt_s8_mhi_resume.py" in text
    assert "06354dfc" in text or "qwen3.5-4b-theology-cpt-lora-v2" in text
    assert "Grok Bot" in text
    assert "vast_cpt_s8_mhi_resume_hf_export_orchestrate.ps1 -Go" in text
    assert "Cursor does not rent" in text
    assert "LOCAL_MERGED_OK" in text


def test_pod_layout_uses_workspace_when_script_is_not_in_repo() -> None:
    script = Path("/workspace/merge_cpt_s8_mhi_resume.py")
    env = {"SFT_WORK_ROOT": "/workspace"}
    paths = merge.default_paths(script, env)
    assert paths["parent"] == Path("/workspace/merge_parent_a70")
    assert paths["resume"] == Path("/workspace/theology_cpt_lora")
    assert paths["intermediate"] == Path("/workspace/theology_cpt_merged_a70")
    assert merge.work_root_for(script, env) == Path("/workspace")
    assert merge.merge_lora_py(script) == Path("/workspace/merge_cpt_lora.py")
    assert merge.repo_root_from_script(script) is None


def test_readiness_flat_workspace_path_does_not_indexerror() -> None:
    """Vast copies readiness flat to /workspace/… — parents[2] must not raise."""
    script = Path("/workspace/cpt_s8_mhi_resume_merge_readiness.py")
    env = {"SFT_WORK_ROOT": "/workspace"}
    assert ready.repo_root_from_script(script) is None
    paths = ready.default_paths(script, env)
    assert paths["parent"] == Path("/workspace/merge_parent_a70")
    assert paths["resume"] == Path("/workspace/theology_cpt_lora")
    assert paths["local_merged"] == Path(
        "/workspace/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit"
    )
    assert paths["merge_py"] == Path("/workspace/merge_cpt_s8_mhi_resume.py")
    # CPT_REPO_ROOT also accepted for pod defaults
    paths_cpt = ready.default_paths(script, {"CPT_REPO_ROOT": "/workspace"})
    assert paths_cpt["parent"] == Path("/workspace/merge_parent_a70")


def test_readiness_repo_layout_keeps_adapter_paths() -> None:
    paths = ready.default_paths(READY_PY, {})
    assert "theology_cpt_lora_s5best" in str(paths["parent"]).replace("\\", "/")
    assert "mhi_resume" in str(paths["resume"]).replace("\\", "/")
    assert "qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit" in str(
        paths["local_merged"]
    ).replace("\\", "/")
    assert ready.repo_root_from_script(READY_PY) == REPO


def test_repo_layout_keeps_adapter_paths_and_honors_work_root() -> None:
    env = {"SFT_WORK_ROOT": "/workspace"}
    paths = merge.default_paths(MERGE_PY, env)
    assert "theology_cpt_lora_s5best" in str(paths["parent"]).replace("\\", "/")
    assert merge.work_root_for(MERGE_PY, env) == Path("/workspace")
    assert merge.work_root_for(MERGE_PY, {}) == REPO / "fine_tuning" / "models"


def test_remote_shell_preflight_passes_adapter_args_and_does_not_upload() -> None:
    text = REMOTE_SH.read_text(encoding="utf-8")
    assert '--preflight "${ARGS[@]}"' in text
    assert "upload_cpt" not in text
    assert "--install" not in text
    assert "unsloth[colab-new]==2026.8.22" in text
    assert "torch==2.8.0" in text
    assert "CPT_S8_MHI_RESUME_MERGE_DONE" in text
    assert "source /workspace/.sft_env" in text


def test_orchestrator_is_merge_fetch_only() -> None:
    text = ORCH_PS1.read_text(encoding="utf-8")
    assert "vast_cpt_s8_mhi_resume_hf_export_session.json" in text
    assert "cpt-s8-mhi-merge-hf" in text
    assert "--check-local" in text
    assert "upload_cpt_s8_mhi_resume_merged_hf.py" not in text
    assert text.index("--check-local") < text.index("vast_destroy.ps1")
    assert "DRY COMPLETE" in text


def test_local_merged_check_rejects_missing(tmp_path: Path) -> None:
    errors = ready.evaluate_local_merged(tmp_path / "missing")
    assert errors
    assert any("missing" in err for err in errors)
