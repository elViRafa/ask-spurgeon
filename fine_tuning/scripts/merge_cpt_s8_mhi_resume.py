#!/usr/bin/env python3
"""Two-stage 16-bit CPT merge for S8 m_hi resume (step 2250).

Stage 1: stock Qwen3.5-4B-Base + P0 s5best LoRA (a70fded8) -> theology_cpt_merged_a70
Stage 2: merged_a70 + resume LoRA (22698039) -> final merged HF folder

Uses merge_cpt_lora.py (Unsloth GPU merge, CPU PEFT fallback). Run on Ampere bf16
(4090 / A100). Do not overwrite Hub production LoRA v2 (06354dfc).

    python fine_tuning/scripts/merge_cpt_s8_mhi_resume.py --preflight
    python fine_tuning/scripts/merge_cpt_s8_mhi_resume.py
    python fine_tuning/scripts/merge_cpt_s8_mhi_resume.py --cpu
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path


def script_parent(script_path: Path) -> Path:
    if script_path.exists():
        return script_path.resolve().parent
    return script_path.parent


def script_in_repo_tree(script_path: Path) -> bool:
    parent = script_parent(script_path)
    return parent.name == "scripts" and parent.parent.name == "fine_tuning"


def repo_root_from_script(script_path: Path) -> Path | None:
    if not script_in_repo_tree(script_path):
        return None
    if script_path.exists():
        return script_path.resolve().parents[2]
    parent = script_parent(script_path)
    return parent.parent.parent


def merge_lora_py(script_path: Path | None = None) -> Path:
    script = Path(__file__) if script_path is None else script_path
    return script_parent(script) / "merge_cpt_lora.py"


def work_root_for(
    script_path: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    """HF cache / subprocess cwd. Pod sets SFT_WORK_ROOT; repo layout is the fallback."""
    script = Path(__file__) if script_path is None else script_path
    env = os.environ if environ is None else environ
    explicit = (env.get("SFT_WORK_ROOT") or "").strip()
    if explicit:
        return Path(explicit)
    repo = repo_root_from_script(script)
    if repo is not None:
        return repo / "fine_tuning" / "models"
    return Path("/workspace")


def default_paths(
    script_file: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Path]:
    """Laptop defaults stay in the repo. A copy at /workspace uses the pod layout."""
    script = Path(__file__) if script_file is None else script_file
    env = os.environ if environ is None else environ
    repo = repo_root_from_script(script)
    if repo is not None:
        return {
            "parent": repo
            / "continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_p0/fetch/theology_cpt_lora_s5best",
            "resume": repo
            / "continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s8_mhi_resume/fetch/mhi_resume/theology_cpt_lora",
            "intermediate": repo / "fine_tuning/models/theology_cpt_merged_a70",
            "final": repo / "fine_tuning/models/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit",
            "staging": repo / "fine_tuning/models/_staging_s8_resume_lora_patched",
        }
    root = Path((env.get("SFT_WORK_ROOT") or "/workspace").strip() or "/workspace")
    return {
        "parent": root / "merge_parent_a70",
        "resume": root / "theology_cpt_lora",
        "intermediate": root / "theology_cpt_merged_a70",
        "final": root / "qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit",
        "staging": root / "_staging_s8_resume_lora_patched",
    }


_PATHS = default_paths()
DEFAULT_PARENT = _PATHS["parent"]
DEFAULT_RESUME = _PATHS["resume"]
DEFAULT_INTERMEDIATE = _PATHS["intermediate"]
DEFAULT_FINAL = _PATHS["final"]
DEFAULT_STAGING = _PATHS["staging"]

SHA_PARENT = "a70fded8aea1c9cb1a484e640e89137412519c28d95bdbfbf8d73ca2d2e42eac"
SHA_RESUME = "2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207"


def _run_merge_cpt_lora(
    work_root: Path,
    adapter: Path,
    merged: Path,
    expected_sha: str,
    cpu: bool,
) -> None:
    env = os.environ.copy()
    env["SFT_WORK_ROOT"] = str(work_root.resolve())
    env["HF_HOME"] = env.get("HF_HOME") or str((work_root / "hf_home").resolve())
    env["SFT_CPT_ADAPTER"] = str(adapter.resolve())
    env["SFT_GATE0_MERGED"] = str(merged.resolve())
    env["EXPECTED_ADAPTER_SHA256"] = expected_sha
    if cpu:
        env["SFT_MERGE_DEVICE"] = "cpu"
    cmd = [sys.executable, "-u", str(merge_lora_py())]
    if cpu:
        cmd.append("--cpu")
    print("RUN", " ".join(cmd))
    print("  SFT_CPT_ADAPTER", env["SFT_CPT_ADAPTER"])
    print("  SFT_GATE0_MERGED", env["SFT_GATE0_MERGED"])
    print("  EXPECTED_ADAPTER_SHA256", expected_sha[:16], "...")
    subprocess.check_call(cmd, env=env, cwd=str(work_root))


def _patch_resume_adapter(resume_dir: Path, merged_base: Path, staging: Path) -> Path:
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(resume_dir, staging)
    cfg_path = staging / "adapter_config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg["base_model_name_or_path"] = str(merged_base.resolve())
    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    return staging


def _preflight_paths(
    parent: Path,
    resume: Path,
    intermediate: Path,
    final: Path,
) -> list[str]:
    errors: list[str] = []
    merge_py = merge_lora_py()
    if not merge_py.is_file():
        errors.append(f"missing merge_cpt_lora.py at {merge_py}")
    pw = parent / "adapter_model.safetensors"
    rw = resume / "adapter_model.safetensors"
    if not pw.is_file():
        errors.append(f"missing merge parent weights {pw}")
    if not rw.is_file():
        errors.append(f"missing resume LoRA weights {rw}")
    if not (resume / "adapter_config.json").is_file():
        errors.append(f"missing {resume / 'adapter_config.json'}")
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from cpt_s8_mhi_resume_merge_readiness import evaluate_merge_paths

    errors.extend(evaluate_merge_paths(parent, resume))
    parent.parent.mkdir(parents=True, exist_ok=True)
    final.parent.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(final.parent).free
    if free < 30 * 1024**3:
        errors.append(f"need >=30 GB free under {final.parent} (have {free // (1024**3)} GB)")
    if intermediate.resolve() == final.resolve():
        errors.append("intermediate and final merge paths must differ")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Two-stage S8 m_hi resume CPT merge (16-bit HF)")
    parser.add_argument("--preflight", action="store_true", help="Check paths/SHA only")
    parser.add_argument("--cpu", action="store_true", help="Force CPU PEFT merge (both stages)")
    parser.add_argument("--parent-adapter", type=Path, default=DEFAULT_PARENT)
    parser.add_argument("--resume-adapter", type=Path, default=DEFAULT_RESUME)
    parser.add_argument("--intermediate", type=Path, default=DEFAULT_INTERMEDIATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_FINAL)
    parser.add_argument("--staging", type=Path, default=DEFAULT_STAGING)
    parser.add_argument("--force", action="store_true", help="Remove existing merge outputs first")
    args = parser.parse_args()

    work_root = work_root_for()
    work_root.mkdir(parents=True, exist_ok=True)

    errors = _preflight_paths(args.parent_adapter, args.resume_adapter, args.intermediate, args.output)
    if errors:
        for err in errors:
            print("preflight FAIL:", err)
        raise SystemExit(1)
    print("preflight paths OK")
    if args.preflight:
        print("Re-run without --preflight on an Ampere GPU to merge.")
        return

    if args.force:
        for path in (args.intermediate, args.output, args.staging):
            if path.is_dir():
                print("Removing", path)
                shutil.rmtree(path)

    if not (args.intermediate / "config.json").is_file():
        print("=== Stage 1: a70 LoRA -> merged_a70 ===")
        _run_merge_cpt_lora(work_root, args.parent_adapter, args.intermediate, SHA_PARENT, args.cpu)
    else:
        print("Stage 1 skip (exists):", args.intermediate)

    if not (args.intermediate / "config.json").is_file():
        raise SystemExit("Stage 1 failed: no config.json in intermediate")

    patched = _patch_resume_adapter(args.resume_adapter, args.intermediate, args.staging)
    print("Patched resume adapter base ->", args.intermediate.resolve())

    if not (args.output / "config.json").is_file():
        print("=== Stage 2: resume LoRA -> final merged 16-bit ===")
        _run_merge_cpt_lora(work_root, patched, args.output, SHA_RESUME, args.cpu)
    else:
        print("Stage 2 skip (exists):", args.output)

    if not (args.output / "config.json").is_file():
        raise SystemExit("Stage 2 failed: no config.json in output")

    print("MERGE_S8_MHI_RESUME_DONE", args.output.resolve())
    print("Next: upload_cpt_s8_mhi_resume_merged_hf.py (see NEXT_CPT_S8_MHI_RESUME_HF_EXPORT.md)")


if __name__ == "__main__":
    main()
