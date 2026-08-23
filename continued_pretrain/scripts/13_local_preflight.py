#!/usr/bin/env python3
"""
Local CPT v2 preflight (no GPU) — partial D1/D2/G2 + share gates before Kaggle.

Reads theology_mix_train.txt + manifest + holdouts, writes:
  continued_pretrain/data/preflight_report.json

Usage:
  python continued_pretrain/scripts/13_local_preflight.py
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

DOC_SEP = "<|endoftext|>"
TARGET_SHARES = {
    "spurgeon": (0.40, 0.50),
    "puritan": (0.30, 0.45),  # slightly wide — corpus still puritan-light vs full plan
    "confession": (0.03, 0.08),
    "bible": (0.02, 0.05),
    "general": (0.08, 0.12),
}
TOKENS_PER_STEP = 16 * 2048  # batch 2 × accum 8 × seq 2048
MAX_DOC_CHARS = 8000


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent.parent))
    args = p.parse_args(argv)
    repo = Path(args.repo_root).resolve()
    data = repo / "continued_pretrain" / "data"
    train = data / "theology_mix_train.txt"
    manifest_path = data / "theology_mix_manifest.json"
    holdouts_dir = data / "holdouts"
    report_path = data / "preflight_report.json"

    errors: list[str] = []
    warnings: list[str] = []
    report: dict = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "plan": "PLAN_FABLE5_TO_IMPROVE_CPT v2",
        "checks": {},
    }

    if not train.exists():
        errors.append(f"missing {train}")
        _write(report_path, report, errors, warnings)
        sys.exit(2)

    text = train.read_text(encoding="utf-8")
    docs = [d.strip() for d in text.split(DOC_SEP) if d.strip()]
    lengths = [len(d) for d in docs]
    over = sum(1 for n in lengths if n > MAX_DOC_CHARS)
    report["checks"]["corpus"] = {
        "train_chars": len(text),
        "n_docs": len(docs),
        "max_doc_chars": max(lengths) if lengths else 0,
        "min_doc_chars": min(lengths) if lengths else 0,
        "p50_doc_chars": int(sorted(lengths)[len(lengths) // 2]) if lengths else 0,
        "docs_over_8k": over,
    }
    if over:
        errors.append(f"F1: {over} docs exceed {MAX_DOC_CHARS} chars")
    else:
        report["checks"]["F1_chunking"] = "PASS — no doc > 8k chars (chunking applied at mix build)"

    # D2-lite: docs themselves should NOT need EOS (A/B append at train time);
    # check that sep exists between docs and count empty holdouts later.
    sep_count = text.count(DOC_SEP)
    report["checks"]["D2_lite"] = {
        "doc_separators": sep_count,
        "docs": len(docs),
        "note": "B_sota APPEND_EOS=True appends tokenizer.eos_token before packing; packed EOS proof still Kaggle D2",
        "status": "PASS" if sep_count >= len(docs) - 1 else "WARN",
    }
    if sep_count < max(0, len(docs) - 1):
        warnings.append("separator count lower than expected vs doc count")

    # G2 + shares from manifest
    if not manifest_path.exists():
        errors.append(f"missing {manifest_path}")
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        buckets = manifest.get("buckets") or {}
        domain = [b for b in ("spurgeon", "puritan", "confession", "bible") if (buckets.get(b) or {}).get("chars", 0) > 0]
        report["checks"]["G2"] = {
            "domain_buckets": domain,
            "status": "PASS" if len(domain) >= 2 else "FAIL",
        }
        if len(domain) < 2:
            errors.append(f"G2: need ≥2 domain buckets, found {domain}")

        share_report = {}
        for name, (lo, hi) in TARGET_SHARES.items():
            info = buckets.get(name) or {}
            share = info.get("char_share")
            if share is None:
                if name == "general":
                    warnings.append("no general/replay bucket in mix")
                    share_report[name] = {"status": "MISSING", "share": None}
                continue
            ok = lo <= float(share) <= hi
            share_report[name] = {"share": share, "target": [lo, hi], "status": "PASS" if ok else "WARN"}
            if not ok:
                warnings.append(f"share {name}={share} outside [{lo},{hi}]")
        report["checks"]["shares"] = share_report

        vt = manifest.get("verified_tokens") or {}
        est_tok = vt.get("train_estimated_tokens") or manifest.get("train_approx_tokens")
        report["checks"]["D3"] = {
            "verified_tokens_present": bool(vt),
            "train_estimated_tokens": est_tok,
            "tokenizer": vt.get("tokenizer"),
            "status": "PASS" if vt else "WARN",
        }
        if not vt:
            warnings.append("D3: run 06_verify_tokens.py --mix to fill verified_tokens")

        # MAX_STEPS recommendation
        if est_tok:
            steps_epoch = max(1, math.ceil(int(est_tok) / TOKENS_PER_STEP))
            report["checks"]["session_budget"] = {
                "tokens_per_step": TOKENS_PER_STEP,
                "steps_per_epoch_est": steps_epoch,
                "recommended_MAX_STEPS": steps_epoch,
                "note": "Measure s/step on Kaggle; if packing yields different row count, recompute from D1 tokens/epoch",
            }

    # Holdouts
    ho = {}
    for name in ("spurgeon", "puritan", "confession", "general"):
        path = holdouts_dir / f"{name}_holdout.txt"
        size = path.stat().st_size if path.exists() else 0
        ho[name] = {"exists": path.exists(), "bytes": size, "status": "PASS" if size > 0 else "FAIL"}
        if size == 0:
            errors.append(f"empty/missing holdout: {name}")
    report["checks"]["holdouts"] = ho

    # Manual holdouts
    manual = data / "holdouts_manual"
    report["checks"]["holdouts_manual"] = {
        "heidelberg": (manual / "heidelberg_catechism.txt").exists(),
        "belgic": (manual / "belgic_confession.txt").exists(),
    }
    if not report["checks"]["holdouts_manual"]["heidelberg"]:
        warnings.append("missing Heidelberg holdout for MCQ generalization")

    # MCQ
    mcq_path = data / "catechism_mcq.json"
    if mcq_path.exists():
        mcq = json.loads(mcq_path.read_text(encoding="utf-8"))
        sets = mcq.get("sets") or {}
        report["checks"]["mcq"] = {k: len(v or []) for k, v in sets.items()}
        if (sets.get("wsc") or sets.get("heidelberg")) is None or (
            len(sets.get("wsc") or []) < 10 or len(sets.get("heidelberg") or []) < 10
        ):
            warnings.append("MCQ sets thin — re-run 09_build_catechism_mcq.py")
    else:
        errors.append("missing catechism_mcq.json")

    # Package zip
    zip_path = data / "kaggle_upload" / "theology-cpt-corpus.zip"
    report["checks"]["kaggle_package"] = {
        "exists": zip_path.exists(),
        "bytes": zip_path.stat().st_size if zip_path.exists() else 0,
        "path": str(zip_path),
    }
    if not zip_path.exists():
        warnings.append("run 12_package_kaggle_corpus.py before upload")

    # M1 file
    m1 = data / "M1_BASE_MODEL_GATE.md"
    report["checks"]["M1_doc"] = m1.exists()
    report["checks"]["Kaggle_only_remaining"] = [
        "D1 packed-row token lengths after Unsloth packing",
        "D2 EOS counts in packed train_dataset",
        "D4 trainable embed/lm_head after get_peft_model",
        "Unsloth hybrid qwen3_5 trainability on T4",
        "G1 pin unsloth commit after first good session",
        "Train 1 epoch + C_sota eval + merge gate",
    ]

    report["errors"] = errors
    report["warnings"] = warnings
    report["overall"] = "FAIL" if errors else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("=" * 60)
    print(f"Preflight: {report['overall']}")
    print(f"  report: {report_path}")
    for e in errors:
        print(f"  ERROR: {e}")
    for w in warnings:
        print(f"  WARN:  {w}")
    sb = report.get("checks", {}).get("session_budget") or {}
    if sb:
        print(f"  MAX_STEPS ≈ {sb.get('recommended_MAX_STEPS')}  (tokens/step={sb.get('tokens_per_step')})")
    print("=" * 60)
    sys.exit(2 if errors else 0)


def _write(path: Path, report: dict, errors: list, warnings: list) -> None:
    report["errors"] = errors
    report["warnings"] = warnings
    report["overall"] = "FAIL"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
