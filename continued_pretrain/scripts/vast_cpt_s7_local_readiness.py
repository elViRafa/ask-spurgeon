#!/usr/bin/env python3
"""Local readiness for Vast CPT S7 P1 (v6_p0 + a70fded8; metric_for_best=eval_puritan_loss). No GPU rent, no train."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CPT = REPO / "continued_pretrain"
S6_LORA = (
    CPT
    / "kaggle"
    / "runpod_cpt_v3"
    / "vast_cpt_s6"
    / "fetch"
    / "theology_cpt_lora"
    / "theology_cpt_lora"
    / "adapter_model.safetensors"
)
S7_S5BEST = (
    CPT
    / "kaggle"
    / "runpod_cpt_v3"
    / "vast_cpt_s7_p0"
    / "fetch"
    / "theology_cpt_lora_s5best"
    / "adapter_model.safetensors"
)
S5_LORA = CPT / "kaggle" / "runpod_cpt_v3" / "theology_cpt_lora" / "adapter_model.safetensors"
META = CPT / "kaggle" / "a_output_v6_p0" / "DATASET_META.json"
DATASET = CPT / "kaggle" / "a_output_v6_p0" / "theology_dataset" / "dataset_dict.json"
HOLDOUT = CPT / "kaggle" / "a_output_v6_p0" / "theology_holdouts" / "spurgeon" / "dataset_info.json"
V6_META = CPT / "kaggle" / "a_output_v6" / "DATASET_META.json"
V5_META = CPT / "kaggle" / "a_output_v5" / "DATASET_META.json"
V4_META = CPT / "kaggle" / "a_output_v4" / "DATASET_META.json"
V3_META = CPT / "kaggle" / "a_output_v3" / "DATASET_META.json"
MANIFEST = CPT / "data" / "mix_v6_p0" / "theology_mix_manifest.json"
REMOTE_SH = CPT / "scripts" / "vast_cpt_s7_remote_continue_b.sh"
TRAIN = CPT / "scripts" / "train_cpt_sota.py"
RUNTIME = CPT / "scripts" / "cpt_runtime.py"
SSH_KEY = Path.home() / ".ssh" / "runpod_cpt"
FETCH_ROOT = CPT / "kaggle" / "runpod_cpt_v3" / "vast_cpt_s7_p0"
SOTA_CKPT = (
    CPT
    / "kaggle"
    / "runpod_cpt_v3"
    / "s6_continue_b"
    / "checkpoints_sota"
    / "checkpoints_sota"
    / "checkpoint-2050"
)

EXPECT_S6 = "6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c"
EXPECT_S5 = "ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303"
EXPECT_S7 = "a70fded8aea1c9cb1a484e640e89137412519c28d95bdbfbf8d73ca2d2e42eac"
EXPECT_S7_PHASE_B = "ddbbee3ac9ef7baf6cca21dcdb844d027d39f5f6a4b88ba10fcf8a43fa7c8214"
EXPECT_S7_PHASE_A = "06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432"
EXPECT_MIX = "ad817213af207428785c4cfac12ddc1bc390b3e59d6e97b43491fafdafe91962"
EXPECT_MIX_V6 = "e050787e138e3d082937e35d1a87aa139f8e980403c3e5fefcc55aa90a2465fc"
EXPECT_MIX_V5 = "61e830575138935cdf6c1b029a3128e096ff4e3633e44a464b3957b9d6e78285"
EXPECT_MIX_V4 = "37a3ba50aa9efb8057d9d36227ac4547f08d35a31ccd71cf3f2d20f928131c81"
EXPECT_MIX_V3 = "23dd3820baa0b657cb6528e4fdf1b2d4813c3cfa7b7c982805b4a7ff34990973"


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
    print("=== Vast CPT S7 P1 local readiness (no rent) ===")

    for p, label in (
        (DATASET, "HF theology_dataset a_output_v6_p0"),
        (HOLDOUT, "HF spurgeon holdout a_output_v6_p0"),
        (META, "DATASET_META.json a_output_v6_p0"),
        (MANIFEST, "mix_v6_p0 theology_mix_manifest.json"),
        (TRAIN, "train_cpt_sota.py"),
        (RUNTIME, "cpt_runtime.py"),
        (REMOTE_SH, "vast_cpt_s7_remote_continue_b.sh"),
        (S7_S5BEST, "P0 best LoRA a70fded8 (checkpoint-600)"),
        (SSH_KEY, "SSH private key"),
    ):
        ok = p.is_file()
        print(f"{'OK' if ok else 'MISSING'} {label}: {p}")
        if not ok:
            errors.append(f"missing {label}")

    if META.is_file():
        meta = json.loads(META.read_text(encoding="utf-8"))
        mix = (meta.get("mix_sha256") or "").lower()
        print(f"mix_sha256={mix[:16]}... expect={EXPECT_MIX[:16]}...")
        if mix != EXPECT_MIX:
            errors.append(f"mix SHA mismatch got {mix}")

    if MANIFEST.is_file():
        man = json.loads(MANIFEST.read_text(encoding="utf-8"))
        sibling = man.get("holdout_sibling") or {}
        share = man.get("holdout_sibling_share")
        buckets = man.get("buckets") or {}
        conf_target = man.get("target_confession_share")
        print(
            f"holdout_sibling_share={share} "
            f"sibling_char_share={sibling.get('sibling_char_share')} "
            f"target_confession_share={conf_target} "
            f"confession={ (buckets.get('confession') or {}).get('char_share') } "
            f"puritan={ (buckets.get('puritan') or {}).get('char_share') } "
            f"spurgeon={ (buckets.get('spurgeon') or {}).get('char_share') }"
        )
        if share != 0.25:
            errors.append(f"mix_v6_p0 holdout_sibling_share want 0.25 got {share}")
        if conf_target != 0.15:
            errors.append(f"mix_v6_p0 target_confession_share want 0.15 got {conf_target}")
        for bucket, want in (("confession", 0.15), ("spurgeon", 0.35), ("puritan", 0.50)):
            got = float((buckets.get(bucket) or {}).get("char_share") or -1)
            if abs(got - want) > 0.01:
                errors.append(f"mix_v6_p0 {bucket} share want ~{want} got {got}")


    if V6_META.is_file():
        v6 = json.loads(V6_META.read_text(encoding="utf-8"))
        v6_mix = (v6.get("mix_sha256") or "").lower()
        print(f"v6_mix_sha256={v6_mix[:16]}... frozen={EXPECT_MIX_V6[:16]}...")
        if v6_mix != EXPECT_MIX_V6:
            errors.append(f"a_output_v6 was mutated got {v6_mix}")
    else:
        errors.append("missing frozen a_output_v6 DATASET_META.json")

    if V5_META.is_file():
        v5 = json.loads(V5_META.read_text(encoding="utf-8"))
        v5_mix = (v5.get("mix_sha256") or "").lower()
        print(f"v5_mix_sha256={v5_mix[:16]}... frozen={EXPECT_MIX_V5[:16]}...")
        if v5_mix != EXPECT_MIX_V5:
            errors.append(f"a_output_v5 was mutated got {v5_mix}")
    else:
        errors.append("missing frozen a_output_v5 DATASET_META.json")

    if V4_META.is_file():
        v4 = json.loads(V4_META.read_text(encoding="utf-8"))
        v4_mix = (v4.get("mix_sha256") or "").lower()
        print(f"v4_mix_sha256={v4_mix[:16]}... frozen={EXPECT_MIX_V4[:16]}...")
        if v4_mix != EXPECT_MIX_V4:
            errors.append(f"a_output_v4 was mutated got {v4_mix}")
    else:
        errors.append("missing frozen a_output_v4 DATASET_META.json")

    if V3_META.is_file():
        v3 = json.loads(V3_META.read_text(encoding="utf-8"))
        v3_mix = (v3.get("mix_sha256") or "").lower()
        print(f"v3_mix_sha256={v3_mix[:16]}... frozen={EXPECT_MIX_V3[:16]}...")
        if v3_mix != EXPECT_MIX_V3:
            errors.append(f"a_output_v3 was mutated got {v3_mix}")
    else:
        errors.append("missing frozen a_output_v3 DATASET_META.json")

    if S7_S5BEST.is_file():
        got = sha256_file(S7_S5BEST).lower()
        print(f"s7_s5best_sha={got[:16]}... size_mb={dir_mb(S7_S5BEST)}")
        if got != EXPECT_S7:
            errors.append(f"S7 s5best SHA mismatch got {got} want {EXPECT_S7}")
        if got == EXPECT_S6:
            errors.append("Init resolved to S6 SHA 6aab — use P0 best a70fded8")
        if got == EXPECT_S7_PHASE_A:
            errors.append("Init resolved to Phase A 06354dfc — use P0 best a70fded8")
        if got == EXPECT_S7_PHASE_B:
            errors.append("Init resolved to Phase B ddbbee3a — use P0 best a70fded8")
        if got == EXPECT_S5:
            errors.append("Phase B init resolved to S5 SHA ef4df3a3 — wrong adapter")

    if S6_LORA.is_file():
        print("NOTE: S6 LoRA still on disk — Phase B pack must use s5best, not 6aab")

    if S5_LORA.is_file():
        s5 = sha256_file(S5_LORA).lower()
        if s5 == EXPECT_S5:
            print("NOTE: S5 LoRA still present at theology_cpt_lora (ef4df3a3) — S7 pack must NOT use it")

    # S7 must NOT require shipping checkpoint-2050
    if SOTA_CKPT.is_dir():
        print(f"NOTE: local checkpoints_sota/checkpoint-2050 exists — S7 pack must exclude it")
    else:
        print("OK no requirement for checkpoint-2050 (S7 new Adam)")

    sh = REMOTE_SH.read_text(encoding="utf-8") if REMOTE_SH.is_file() else ""
    for needle in (
        "CPT_CONTINUE_PROFILE=s7",
        "ENV_NAME=unsloth_cpt_s7",
        "PREV_RUN_CHECKPOINT=",
        "a70fded8aea1c9cb1a484e640e89137412519c28d95bdbfbf8d73ca2d2e42eac",
        "COMPOSITE_EARLY_STOP_METRICS",
        "METRIC_FOR_BEST",
        "eval_puritan_loss",
        'nohup env',
    ):
        if needle not in sh:
            errors.append(f"remote launcher missing {needle!r}")
    if "eval_mix_loss" in sh:
        errors.append("remote launcher must drop eval_mix_loss from the halt composite")
    if "torch==2.11" in sh or "unsloth.git" in sh:
        errors.append("remote launcher must not use torch 2.11 or floating unsloth.git")
    if 'python3 -u /workspace/train_cpt_sota.py' in sh:
        errors.append("remote launcher must use conda $PY, not system python3")

    Fetch_root = FETCH_ROOT
    Fetch_root.mkdir(parents=True, exist_ok=True)
    print(f"results_dir={Fetch_root} free_c={disk_free_gb('C')}GB")

    if errors:
        print("FAIL:")
        for e in errors:
            print(" -", e)
        return 1
    for w in warnings:
        print("WARN:", w)
    print("READY: Vast S7 P1 local artifacts OK (no rent; operator go to copy v6_p0 + a70fded8)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
