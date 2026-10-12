#!/usr/bin/env python3
"""Local readiness for S8 m_hi resume two-stage 16-bit merge. No GPU rent."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
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


def default_paths(
    script_file: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Path]:
    """Laptop defaults stay in the repo. A flat copy at /workspace uses the pod layout."""
    script = Path(__file__) if script_file is None else script_file
    env = os.environ if environ is None else environ
    repo = repo_root_from_script(script)
    if repo is not None:
        return {
            "parent": repo
            / "continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_p0/fetch/theology_cpt_lora_s5best",
            "resume": repo
            / "continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s8_mhi_resume/fetch/mhi_resume/theology_cpt_lora",
            "local_merged": repo
            / "fine_tuning/models/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit",
            "merge_py": repo / "fine_tuning/scripts/merge_cpt_s8_mhi_resume.py",
        }
    root = Path(
        (env.get("CPT_REPO_ROOT") or env.get("SFT_WORK_ROOT") or "/workspace").strip()
        or "/workspace"
    )
    return {
        "parent": root / "merge_parent_a70",
        "resume": root / "theology_cpt_lora",
        "local_merged": root / "qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit",
        "merge_py": root / "merge_cpt_s8_mhi_resume.py",
    }


_PATHS = default_paths()
DEFAULT_PARENT = _PATHS["parent"]
DEFAULT_RESUME = _PATHS["resume"]
DEFAULT_LOCAL_MERGED = _PATHS["local_merged"]
# Kept for callers that still expect REPO; None when running as a flat /workspace copy.
REPO = repo_root_from_script(Path(__file__))

SHA_PARENT = "a70fded8aea1c9cb1a484e640e89137412519c28d95bdbfbf8d73ca2d2e42eac"
SHA_RESUME = "2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207"
PHASE_A = "06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432"
MIN_MERGED_SHARD_BYTES = 7 * 1024**3


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate_merge_paths(parent: Path, resume: Path) -> list[str]:
    errors: list[str] = []
    pw = parent / "adapter_model.safetensors"
    rw = resume / "adapter_model.safetensors"
    if pw.is_file():
        got = sha256_file(pw)
        if got.lower() != SHA_PARENT.lower():
            errors.append(f"merge parent SHA mismatch want {SHA_PARENT[:16]}… got {got[:16]}…")
    if rw.is_file():
        got = sha256_file(rw)
        if got.lower() != SHA_RESUME.lower():
            errors.append(f"resume LoRA SHA mismatch want {SHA_RESUME[:16]}… got {got[:16]}…")
        if got.lower() == PHASE_A.lower():
            errors.append("resume path is Phase A Hub 06354dfc — use m_hi resume 22698039")
    cfg_path = resume / "adapter_config.json"
    if cfg_path.is_file():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        base = str(cfg.get("base_model_name_or_path") or "")
        if "theology_cpt_merged_a70" not in base:
            errors.append(f"resume adapter_config base must be merged a70, got {base!r}")
        if cfg.get("r") != 128 or cfg.get("lora_alpha") != 64:
            errors.append(f"expected r=128 alpha=64, got r={cfg.get('r')} alpha={cfg.get('lora_alpha')}")
    return errors


def evaluate_local_merged(path: Path) -> list[str]:
    """Read-only check of a fetched 16-bit folder. Empty list means complete."""
    errors: list[str] = []
    if not path.is_dir():
        return [f"merged folder missing: {path}"]
    if not (path / "config.json").is_file():
        errors.append(f"missing config.json in {path}")
    tok_ok = any(
        (path / name).is_file()
        for name in ("tokenizer.json", "tokenizer.model", "tokenizer_config.json")
    )
    if not tok_ok:
        errors.append(f"missing tokenizer files in {path}")
    shards = [p for p in path.glob("*.safetensors") if p.is_file()]
    if not shards:
        errors.append(f"no .safetensors shards in {path}")
    else:
        total = sum(p.stat().st_size for p in shards)
        if total < MIN_MERGED_SHARD_BYTES:
            gib = total / (1024**3)
            errors.append(f"safetensors total {gib:.2f} GiB is below 7 GiB (partial fetch)")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="S8 m_hi resume merge readiness (no GPU)")
    parser.add_argument(
        "--check-local",
        action="store_true",
        help="Check the fetched 16-bit folder only. Does not contact Vast or Hugging Face.",
    )
    parser.add_argument("--merged-path", type=Path, default=DEFAULT_LOCAL_MERGED)
    args = parser.parse_args()

    if args.check_local:
        errors = evaluate_local_merged(args.merged_path)
        if errors:
            for err in errors:
                print("LOCAL_MERGED_NOT_READY:", err)
            return 1
        print("LOCAL_MERGED_OK", args.merged_path.resolve())
        return 0

    paths = default_paths()
    errors = evaluate_merge_paths(paths["parent"], paths["resume"])
    merge_py = paths["merge_py"]
    if not merge_py.is_file():
        errors.append(f"missing {merge_py}")
    if errors:
        for err in errors:
            print("NOT READY:", err)
        return 1
    print("READY merge parent + resume LoRA paths and SHAs")
    print("  parent", paths["parent"])
    print("  resume", paths["resume"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
