#!/usr/bin/env python3
"""
Push CPT v2 notebooks to Kaggle and run them (requires `kaggle auth login`).

Steps:
  1. Create/update dataset rafaelvieira1/theology-cpt-corpus
  2. Push + run A_data_prep_sota kernel
  3. Download A output -> create theology-cpt-dataset
  4. Push + run B_training_sota kernel (GPU T4)

Usage:
  python continued_pretrain/scripts/15_push_kaggle_cpt.py
  python continued_pretrain/scripts/15_push_kaggle_cpt.py --skip-a   # if dataset already exists
  python continued_pretrain/scripts/15_push_kaggle_cpt.py --only-a
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

KAGGLE_USER = "rafaelvieira1"
CORPUS_SLUG = f"{KAGGLE_USER}/theology-cpt-corpus"
DATASET_SLUG = f"{KAGGLE_USER}/theology-cpt-dataset"
KERNEL_A = f"{KAGGLE_USER}/theology-cpt-v2-a-data-prep-sota"
KERNEL_B = f"{KAGGLE_USER}/theology-cpt-v2-b-training-sota"
KERNEL_C = f"{KAGGLE_USER}/theology-cpt-v2-c-eval-sota"


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=cwd)


def kaggle(*args: str) -> None:
    run([sys.executable, "-m", "kaggle", *args])


def auth_check() -> None:
    try:
        kaggle("datasets", "list", "--max-size", "1")
    except subprocess.CalledProcessError as e:
        raise SystemExit(
            "Kaggle not authenticated. Run: python -m kaggle auth login"
        ) from e


def stage_corpus(staging: Path, repo: Path) -> None:
    data = repo / "continued_pretrain" / "data"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    holdouts = staging / "holdouts"
    holdouts.mkdir()
    for name in [
        "theology_mix_train.txt",
        "theology_mix_manifest.json",
        "catechism_mcq.json",
        "M1_BASE_MODEL_GATE.md",
    ]:
        shutil.copy2(data / name, staging / name)
    for h in (data / "holdouts").glob("*_holdout.txt"):
        shutil.copy2(h, holdouts / h.name)
    meta = {
        "title": "theology-cpt-corpus",
        "id": CORPUS_SLUG,
        "licenses": [{"name": "CC0-1.0"}],
    }
    (staging / "dataset-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def corpus_exists() -> bool:
    try:
        kaggle("datasets", "files", CORPUS_SLUG, "--page-size", "1")
        return True
    except subprocess.CalledProcessError:
        return False


def upload_corpus(staging: Path) -> None:
    if corpus_exists():
        print(f"Updating dataset {CORPUS_SLUG}")
        kaggle("datasets", "version", "-p", str(staging), "-m", "CPT v2 corpus refresh", "--dir-mode", "tar")
    else:
        print(f"Creating dataset {CORPUS_SLUG}")
        kaggle("datasets", "create", "-p", str(staging), "--dir-mode", "tar")


def stage_kernel(staging: Path, notebook: Path, meta: dict) -> None:
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    shutil.copy2(notebook, staging / notebook.name)
    (staging / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def wait_kernel(slug: str, poll_s: int = 60, max_wait_s: int = 7200) -> str:
    print(f"Waiting for kernel {slug} ...")
    deadline = time.time() + max_wait_s
    while time.time() < deadline:
        proc = subprocess.run(
            [sys.executable, "-m", "kaggle", "kernels", "status", slug],
            capture_output=True,
            text=True,
        )
        out = (proc.stdout + proc.stderr).strip()
        print(out)
        lower = out.lower()
        if "complete" in lower and "error" not in lower:
            return "complete"
        if any(x in lower for x in ("error", "failed", "cancelled")):
            return "failed"
        time.sleep(poll_s)
    return "timeout"


def dataset_slug_exists(slug: str) -> bool:
    try:
        kaggle("datasets", "files", slug, "--page-size", "1")
        return True
    except subprocess.CalledProcessError:
        return False


def publish_a_output(repo: Path, dl_dir: Path) -> None:
    if dl_dir.exists():
        shutil.rmtree(dl_dir)
    dl_dir.mkdir(parents=True)
    kaggle("kernels", "output", KERNEL_A, "-p", str(dl_dir))
    staging = repo / "continued_pretrain" / "kaggle" / "theology-cpt-dataset"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    for folder in ["theology_dataset", "theology_holdouts"]:
        src = dl_dir / folder
        if not src.exists():
            raise SystemExit(f"A output missing {folder} under {dl_dir}")
        shutil.copytree(src, staging / folder)
    meta = {
        "title": "theology-cpt-dataset",
        "id": DATASET_SLUG,
        "licenses": [{"name": "CC0-1.0"}],
    }
    (staging / "dataset-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    if dataset_slug_exists(DATASET_SLUG):
        print(f"Updating dataset {DATASET_SLUG}")
        kaggle(
            "datasets",
            "version",
            "-p",
            str(staging),
            "-m",
            "CPT expanded corpus HF refresh",
            "--dir-mode",
            "tar",
        )
    else:
        kaggle("datasets", "create", "-p", str(staging))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--only-a", action="store_true")
    p.add_argument("--only-c", action="store_true", help="Push and run C_eval_sota only")
    p.add_argument("--skip-a", action="store_true", help="Skip A if theology-cpt-dataset exists")
    p.add_argument("--skip-corpus", action="store_true")
    args = p.parse_args(argv)

    repo = Path(__file__).resolve().parent.parent.parent
    kaggle_root = repo / "continued_pretrain" / "kaggle"
    auth_check()

    if args.only_c:
        nb_dir = repo / "continued_pretrain" / "notebooks"
        c_staging = kaggle_root / "C_eval_sota"
        stage_kernel(
            c_staging,
            nb_dir / "C_eval_sota.ipynb",
            {
                "id": KERNEL_C,
                "title": "Theology CPT v2 C Eval SOTA",
                "code_file": "C_eval_sota.ipynb",
                "language": "python",
                "kernel_type": "notebook",
                "is_private": "true",
                "enable_gpu": "true",
                "enable_internet": "true",
                "machine_shape": "NvidiaTeslaT4",
                "dataset_sources": [CORPUS_SLUG],
                "kernel_sources": [KERNEL_B],
            },
        )
        kaggle("kernels", "push", "-p", str(c_staging), "--accelerator", "NvidiaTeslaT4")
        print(f"Pushed C: https://www.kaggle.com/code/{KERNEL_C}")
        return 0

    if not args.skip_corpus:
        corpus_staging = kaggle_root / "theology-cpt-corpus"
        stage_corpus(corpus_staging, repo)
        upload_corpus(corpus_staging)

    nb_dir = repo / "continued_pretrain" / "notebooks"

    if not args.skip_a:
        a_staging = kaggle_root / "A_data_prep_sota"
        stage_kernel(
            a_staging,
            nb_dir / "A_data_prep_sota.ipynb",
            {
                "id": KERNEL_A,
                "title": "Theology CPT v2 A Data Prep SOTA",
                "code_file": "A_data_prep_sota.ipynb",
                "language": "python",
                "kernel_type": "notebook",
                "is_private": "true",
                "enable_gpu": "false",
                "enable_internet": "false",
                "dataset_sources": [CORPUS_SLUG],
            },
        )
        kaggle("kernels", "push", "-p", str(a_staging))
        status = wait_kernel(KERNEL_A, max_wait_s=3600)
        if status != "complete":
            print(f"A kernel ended: {status}", file=sys.stderr)
            kaggle("kernels", "logs", KERNEL_A)
            return 1
        publish_a_output(repo, kaggle_root / "a_output")

    if args.only_a:
        print("Done (--only-a).")
        return 0

    if not dataset_slug_exists(DATASET_SLUG):
        print(f"ERROR: {DATASET_SLUG} missing. Run A first.", file=sys.stderr)
        return 2

    # enable_gpu alone defaults to P100 (sm_60) — broken with Kaggle's torch cu128.
    # machine_shape NvidiaTeslaT4 is required (T4 / sm_75).
    b_staging = kaggle_root / "B_training_sota"
    stage_kernel(
        b_staging,
        nb_dir / "B_training_sota.ipynb",
        {
            "id": KERNEL_B,
            "title": "Theology CPT v2 B Training SOTA",
            "code_file": "B_training_sota.ipynb",
            "language": "python",
            "kernel_type": "notebook",
            "is_private": "true",
            "enable_gpu": "true",
            "enable_internet": "true",
            "machine_shape": "NvidiaTeslaT4",
            "dataset_sources": [CORPUS_SLUG, DATASET_SLUG],
            "kernel_sources": [KERNEL_B],
        },
    )
    kaggle("kernels", "push", "-p", str(b_staging), "--accelerator", "NvidiaTeslaT4")
    status = wait_kernel(KERNEL_B, poll_s=120, max_wait_s=28800)
    if status != "complete":
        print(f"B kernel ended: {status}", file=sys.stderr)
        kaggle("kernels", "logs", KERNEL_B)
        return 1

    print(f"\nSUCCESS")
    print(f"  A: https://www.kaggle.com/code/{KERNEL_A}")
    print(f"  B: https://www.kaggle.com/code/{KERNEL_B}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
