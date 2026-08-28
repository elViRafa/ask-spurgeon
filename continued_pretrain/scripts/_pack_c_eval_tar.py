#!/usr/bin/env python3
"""Build the Runpod C-eval payload tarball. Not part of training."""
from pathlib import Path
import tarfile

root = Path(__file__).resolve().parent.parent
out = root / "kaggle" / "runpod_cpt_v2" / "cpt_c_eval.tar"
items = [
    (root / "kaggle/runpod_cpt_v2/theology_cpt_lora", "theology_cpt_lora"),
    (root / "kaggle/a_output/theology_holdouts", "theology_holdouts"),
    (root / "data/catechism_mcq.json", "catechism_mcq.json"),
    (root / "scripts/eval_cpt_sota.py", "eval_cpt_sota.py"),
]
for src, _name in items:
    if not src.exists():
        raise SystemExit(f"missing {src}")
if out.exists():
    out.unlink()
print("writing", out)
with tarfile.open(out, "w") as tar:
    for src, name in items:
        tar.add(src, arcname=name)
        print(" added", name)
print("tar_bytes", out.stat().st_size)
