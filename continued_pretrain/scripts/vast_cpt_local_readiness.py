#!/usr/bin/env python3
"""Local readiness for Vast CPT S6 continue-B (full corpus v3). No GPU rent, no train."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CPT = REPO / "continued_pretrain"
CKPT = (
    CPT
    / "kaggle"
    / "runpod_cpt_v3"
    / "s6_continue_b"
    / "checkpoints_sota"
    / "checkpoints_sota"
    / "checkpoint-2050"
)
S5 = CPT / "kaggle" / "runpod_cpt_v3" / "theology_cpt_lora" / "adapter_model.safetensors"
MIX_TXT = CPT / "data" / "theology_mix_train.txt"
META = CPT / "kaggle" / "a_output_v3" / "DATASET_META.json"
DATASET = CPT / "kaggle" / "a_output_v3" / "theology_dataset" / "dataset_dict.json"
HOLDOUT = CPT / "kaggle" / "a_output_v3" / "theology_holdouts" / "spurgeon" / "dataset_info.json"
MANIFEST = CPT / "data" / "theology_mix_manifest.json"
REMOTE_SH = CPT / "scripts" / "vast_cpt_remote_continue_b.sh"
TRAIN = CPT / "scripts" / "train_cpt_sota.py"
RUNTIME = CPT / "scripts" / "cpt_runtime.py"
SSH_KEY = Path.home() / ".ssh" / "runpod_cpt"
FETCH_ROOT = CPT / "kaggle" / "runpod_cpt_v3" / "vast_cpt_s6"

EXPECT_S5 = "ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303"
EXPECT_MIX = "23dd3820baa0b657cb6528e4fdf1b2d4813c3cfa7b7c982805b4a7ff34990973"
REQUIRED_CKPT = (
    "trainer_state.json",
    "adapter_model.safetensors",
    "adapter_config.json",
    "optimizer.pt",
    "scheduler.pt",
    "rng_state.pth",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def dir_mb(path: Path) -> float:
    if not path.exists():
        return -1.0
    if path.is_file():
        return round(path.stat().st_size / 1e6, 1)
    total = sum(p.stat().st_size for p in path.rglob("*") if p.is_file())
    return round(total / 1e6, 1)


def disk_free_gb(letter: str) -> float | None:
    usage = shutil.disk_usage(f"{letter}:\\")
    return round(usage.free / (1024**3), 1)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    print("=== Vast CPT S6 local readiness (no rent) ===")

    for p, label in (
        (DATASET, "HF theology_dataset"),
        (HOLDOUT, "HF spurgeon holdout"),
        (META, "DATASET_META.json"),
        (MANIFEST, "theology_mix_manifest.json"),
        (S5, "S5 adapter_model.safetensors"),
        (CKPT, "checkpoint-2050 dir"),
        (MIX_TXT, "theology_mix_train.txt"),
        (TRAIN, "train_cpt_sota.py"),
        (RUNTIME, "cpt_runtime.py"),
        (REMOTE_SH, "vast_cpt_remote_continue_b.sh"),
    ):
        ok = p.exists()
        print(f"{'OK' if ok else 'MISSING'}  {label}: {p}")
        if not ok:
            errors.append(f"missing {label}: {p}")

    if not SSH_KEY.exists() or not Path(str(SSH_KEY) + ".pub").exists():
        errors.append(f"missing SSH key pair {SSH_KEY}")
    else:
        print(f"OK  ssh key {SSH_KEY}")

    print("\n=== sizes MB ===")
    print("a_output_v3", dir_mb(CPT / "kaggle" / "a_output_v3"))
    print("checkpoint-2050", dir_mb(CKPT))
    print("S5 adapter dir", dir_mb(S5.parent))
    print("mix txt", dir_mb(MIX_TXT))

    if CKPT.is_dir():
        names = {p.name for p in CKPT.iterdir()}
        missing = [n for n in REQUIRED_CKPT if n not in names]
        if missing:
            errors.append(f"checkpoint-2050 missing {missing}")
        else:
            print("OK  checkpoint-2050 required files present")
        ts = CKPT / "trainer_state.json"
        if ts.exists():
            d = json.loads(ts.read_text(encoding="utf-8"))
            step = d.get("global_step")
            mx = d.get("max_steps")
            print("global_step", step, "max_steps", mx, "best_metric", d.get("best_metric"))
            if step != 2050:
                warnings.append(f"checkpoint global_step={step} expected 2050")
            if mx != 4128:
                warnings.append(f"checkpoint max_steps={mx} expected 4128")
    ckpt2100 = (
        CPT
        / "kaggle"
        / "runpod_cpt_v3"
        / "s6_continue_b"
        / "checkpoints_sota"
        / "checkpoint-2100"
    )
    if not ckpt2100.exists():
        warnings.append("checkpoint-2100 not local — resume from complete checkpoint-2050")

    if S5.exists():
        got = sha256_file(S5)
        print("S5 sha256", got)
        if got != EXPECT_S5:
            errors.append("S5 adapter SHA256 mismatch")
        else:
            print("OK  S5 SHA256")
    if MIX_TXT.exists():
        gotm = sha256_file(MIX_TXT)
        print("mix sha256", gotm)
        if gotm != EXPECT_MIX:
            errors.append("mix txt SHA256 mismatch")
        else:
            print("OK  mix SHA256")
    if META.exists():
        meta = json.loads(META.read_text(encoding="utf-8"))
        print("hf_train_docs", meta.get("hf_train_docs"), "verified_tokens", meta.get("verified_tokens"))
        if meta.get("mix_sha256") != EXPECT_MIX:
            errors.append("DATASET_META mix_sha256 mismatch")
        if int(meta.get("hf_train_docs") or 0) != 51417:
            warnings.append(f"hf_train_docs={meta.get('hf_train_docs')} expected 51417")

    try:
        from datasets import load_from_disk  # type: ignore

        ds = load_from_disk(str(CPT / "kaggle" / "a_output_v3" / "theology_dataset"))
        n_train = len(ds["train"]) if "train" in ds else -1
        n_val = len(ds["test"] if "test" in ds else ds.get("validation", []))
        print("HF load_from_disk train", n_train, "val/test", n_val)
        if n_train != 51417:
            errors.append(f"HF train rows {n_train} != 51417")
    except Exception as exc:
        warnings.append(f"could not load_from_disk theology_dataset: {exc}")

    c_free = disk_free_gb("C")
    d_free = disk_free_gb("D")
    print(f"\nC: free={c_free}GB  D: free={d_free}GB")
    if c_free is not None and c_free < 15:
        warnings.append(
            f"C: only {c_free}GB free — train assets + fetch live on C: at {FETCH_ROOT}"
        )
    FETCH_ROOT.mkdir(parents=True, exist_ok=True)
    print("OK  fetch root", FETCH_ROOT)
    payload = FETCH_ROOT / "payload.tar"
    if payload.exists():
        print("OK  payload.tar", round(payload.stat().st_size / 1e6, 1), "MB")
    else:
        warnings.append("payload.tar not packed yet — run vast_cpt_pack_payload.ps1 before -Go for faster scp")

    remote_txt = REMOTE_SH.read_text(encoding="utf-8") if REMOTE_SH.exists() else ""
    if "python3 -u /workspace/train_cpt_sota.py" in remote_txt:
        errors.append("remote launcher still uses system python3 (SIGSEGV on Vast)")
    if "ENV_NAME=unsloth_cpt" not in remote_txt and REMOTE_SH.exists():
        errors.append("remote launcher missing Miniforge env unsloth_cpt")
    if "S6_FRESH_START" in remote_txt and "DO NOT" not in remote_txt:
        pass

    if warnings:
        print("\nWARN:")
        for w in warnings:
            print(" -", w)
    if errors:
        print("\nERROR:")
        for e in errors:
            print(" -", e)
        print("\nVast CPT local readiness: FAIL")
        return 2
    print("\nVast CPT local readiness: PASS")
    print("Next session (operator go): cd continued_pretrain\\scripts; .\\vast_cpt_orchestrate.ps1 -Go")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
