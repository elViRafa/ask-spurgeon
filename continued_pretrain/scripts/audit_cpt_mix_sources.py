#!/usr/bin/env python3
"""Corpus-wide CPT mix audit. No GPU. Does not rewrite holdouts.

Checks every tree 07_build_theology_mix.py loads: Puritans (old + new authors),
hymns, confessions, Bible, Spurgeon concat, and general replay.

Exit 0 when the v4 shelf is clean and the v5 reweight pack is CONTINUE_READY.
Exit 2 when a source rewrite / mix rebuild is required, or a pin is broken.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
REPO = SCRIPTS.parent.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import normalize_early_modern_orthography as ortho  # noqa: E402

EXPECT_MIX_V5 = "61e830575138935cdf6c1b029a3128e096ff4e3633e44a464b3957b9d6e78285"
EXPECT_MIX_V4 = "37a3ba50aa9efb8057d9d36227ac4547f08d35a31ccd71cf3f2d20f928131c81"
EXPECT_MIX_V3 = "23dd3820baa0b657cb6528e4fdf1b2d4813c3cfa7b7c982805b4a7ff34990973"
PIN_PURITAN_SHA = "e203eec759365aafb84be29c23b0dc8ff224d142aab9e14629154783e193184f"
PIN_CONFESSION_SHA = "14beb18998272fbcb09ee90571b44cb1b813ad5a0ce1dc2d0e15e9580768127e"

NEW_AUTHOR_FILES = (
    ("downame", "christian_warfare.txt"),
    ("downame", "guide_to_godliness.txt"),
    ("ambrose", "looking_unto_jesus.txt"),
    ("swinnock", "works_1665.txt"),
    ("swinnock", "incomparableness_of_god.txt"),
    ("venning", "plague_of_plagues.txt"),
    ("binning", "sinners_sanctuary.txt"),
    ("preston", "breastplate_of_faith_and_love.txt"),
    ("durham", "unsearchable_riches_of_christ.txt"),
    ("vincent", "true_christians_love_of_the_unseen_christ.txt"),
    ("guthrie", "christians_great_interest.txt"),
)
S5_ABSENT = (
    REPO / "data" / "confessions" / "systematic" / "shaw_exposition_wcf.txt",
    REPO / "data" / "confessions" / "westminster" / "sum_of_saving_knowledge.txt",
)
LEAK_BUCKETS = frozenset({"spurgeon_train", "spurgeon_holdout"})


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_fetch_mod():
    spec = importlib.util.spec_from_file_location(
        "fetch_puritans", SCRIPTS / "10_fetch_puritans.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load 10_fetch_puritans.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def bucket_label(path: Path) -> str:
    rel = path.relative_to(REPO).as_posix()
    if rel.startswith("data/puritans/"):
        return "puritans"
    if rel.startswith("data/confessions/"):
        return "confessions"
    if rel.startswith("data/hymns/"):
        return "hymns"
    if rel.startswith("data/bible/"):
        return "bible"
    if path.name == "general_replay.txt":
        return "replay"
    if path.name == "spurgeon_train.txt":
        return "spurgeon_train"
    if path.name == "spurgeon_holdout.txt":
        return "spurgeon_holdout"
    if "holdouts_pinned_v3" in path.parts:
        return "holdouts_pinned"
    if "holdouts" in path.parts:
        return "holdouts_live"
    return "other"


def audit_sources() -> dict:
    fetch = load_fetch_mod()
    errors: list[str] = []
    warnings: list[str] = []
    glyph_by_bucket: dict[str, int] = {}
    leak_files: list[str] = []
    ocr_fail: list[str] = []
    gutenberg_on_disk: list[str] = []

    paths = ortho.collect_mix_source_paths(REPO, include_holdouts=False)
    print(f"mix_source_files={len(paths)}")
    for path in paths:
        raw = path.read_text(encoding="utf-8", errors="replace")
        label = bucket_label(path)
        if ortho.has_mapped_glyph(raw):
            glyph_by_bucket[label] = glyph_by_bucket.get(label, 0) + 1
            if label in LEAK_BUCKETS:
                leak_files.append(str(path.relative_to(REPO)))
        ok, reason = fetch.ocr_quality_ok(raw)
        if not ok:
            ocr_fail.append(f"{path.relative_to(REPO)} ({reason})")
        head = raw[:8000].upper()
        if "START OF THE PROJECT GUTENBERG" in head or "START OF THIS PROJECT GUTENBERG" in head:
            gutenberg_on_disk.append(str(path.relative_to(REPO)))

    print("glyph_files_by_bucket", glyph_by_bucket or "{}")
    print(f"ocr_fail={len(ocr_fail)}")
    print(f"gutenberg_banners_on_disk={len(gutenberg_on_disk)}")
    for item in gutenberg_on_disk:
        print(f"  gutenberg {item}")

    if ocr_fail:
        errors.extend(f"OCR {row}" for row in ocr_fail)
    if leak_files:
        errors.extend(
            f"mapped glyphs leak into mix (Spurgeon concat not cleaned): {row}"
            for row in leak_files
        )
    elif glyph_by_bucket:
        warnings.append(
            "train-book glyphs remain on disk; clean_generic_text strips them at mix time"
        )

    catalog_ok = 0
    catalog_fail: list[str] = []
    catalog_missing = 0
    for key, entry in fetch.CATALOG.items():
        dest = fetch.entry_dest(REPO, entry)
        if not dest.exists():
            catalog_missing += 1
            continue
        text = dest.read_text(encoding="utf-8", errors="replace")
        if fetch.verify(text, entry):
            catalog_ok += 1
        else:
            catalog_fail.append(key)
    print(
        f"catalog_ok={catalog_ok} catalog_fail={len(catalog_fail)} "
        f"catalog_missing={catalog_missing}"
    )
    if catalog_fail:
        errors.extend(f"catalog identity fail {key}" for key in catalog_fail)

    missing_new = []
    new_dirty = []
    for author, filename in NEW_AUTHOR_FILES:
        dest = REPO / "data" / "puritans" / author / filename
        if not dest.is_file():
            missing_new.append(f"{author}/{filename}")
            continue
        raw = dest.read_text(encoding="utf-8", errors="replace")
        if ortho.has_mapped_glyph(raw):
            new_dirty.append(f"{author}/{filename}")
    print(f"new_author_files={len(NEW_AUTHOR_FILES) - len(missing_new)}/{len(NEW_AUTHOR_FILES)}")
    if missing_new:
        errors.extend(f"missing new-author file {row}" for row in missing_new)
    if new_dirty:
        errors.extend(f"new-author glyphs {row}" for row in new_dirty)

    for path in S5_ABSENT:
        if path.exists():
            errors.append(f"confession S5 present (must stay unfetched): {path.relative_to(REPO)}")
        else:
            print(f"OK S5 absent {path.name}")

    return {
        "errors": errors,
        "warnings": warnings,
        "glyph_by_bucket": glyph_by_bucket,
        "gutenberg_on_disk": gutenberg_on_disk,
        "catalog_ok": catalog_ok,
        "catalog_fail": catalog_fail,
    }


def audit_pins_and_packs() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    holdouts = REPO / "continued_pretrain" / "data" / "holdouts"
    pinned = REPO / "continued_pretrain" / "data" / "holdouts_pinned_v3"
    for name, expect in (
        ("puritan_holdout.txt", PIN_PURITAN_SHA),
        ("confession_holdout.txt", PIN_CONFESSION_SHA),
    ):
        live = holdouts / name
        pin = pinned / name
        if not live.is_file() or not pin.is_file():
            errors.append(f"missing holdout {name}")
            continue
        live_sha = sha256_file(live)
        pin_sha = sha256_file(pin)
        print(f"{name} live={live_sha[:16]} pin={pin_sha[:16]}")
        if live.read_bytes() != pin.read_bytes():
            errors.append(f"live holdout drifted from pin: {name}")
        if pin_sha != expect:
            errors.append(f"pinned SHA mismatch {name} got {pin_sha}")
        live_text = live.read_text(encoding="utf-8", errors="replace")
        if "\u017f" in live_text or "\u017F" in live_text:
            warnings.append(
                f"{name} still has long-s ({live_text.count(chr(0x17F))} chars); "
                "leave pinned for C comparability"
            )

    mix = REPO / "continued_pretrain" / "data" / "theology_mix_train.txt"
    v5_mix = REPO / "continued_pretrain" / "data" / "mix_v5" / "theology_mix_train.txt"
    v5_meta = REPO / "continued_pretrain" / "kaggle" / "a_output_v5" / "DATASET_META.json"
    v4_meta = REPO / "continued_pretrain" / "kaggle" / "a_output_v4" / "DATASET_META.json"
    v3_meta = REPO / "continued_pretrain" / "kaggle" / "a_output_v3" / "DATASET_META.json"
    if not mix.is_file():
        errors.append("missing theology_mix_train.txt")
    else:
        mix_sha = sha256_file(mix)
        print(f"live_mix_sha256={mix_sha}")
        if mix_sha != EXPECT_MIX_V4:
            errors.append(f"live mix SHA {mix_sha} != locked v4 {EXPECT_MIX_V4}")
        raw = mix.read_text(encoding="utf-8", errors="replace")
        leftover = sum(raw.count(ch) for ch in ortho.MAPPED_GLYPHS)
        print(f"live_mix_mapped_glyphs={leftover}")
        if leftover:
            errors.append("packed mix still contains mapped glyphs")

    if not v5_mix.is_file():
        errors.append("missing mix_v5 theology_mix_train.txt")
    else:
        v5_sha = sha256_file(v5_mix)
        print(f"v5_mix_sha256={v5_sha}")
        if v5_sha != EXPECT_MIX_V5:
            errors.append(f"v5 mix SHA {v5_sha} != locked {EXPECT_MIX_V5}")

    for label, path, expect in (
        ("v5", v5_meta, EXPECT_MIX_V5),
        ("v4", v4_meta, EXPECT_MIX_V4),
        ("v3", v3_meta, EXPECT_MIX_V3),
    ):
        if not path.is_file():
            errors.append(f"missing {label} DATASET_META.json")
            continue
        meta = json.loads(path.read_text(encoding="utf-8"))
        got = (meta.get("mix_sha256") or "").lower()
        print(f"{label}_meta_sha={got}")
        if got != expect:
            errors.append(f"{label} DATASET_META mix_sha256 {got} != {expect}")

    return errors, warnings


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    print("=== CPT mix source audit (no rewrite, no GPU) ===")
    source = audit_sources()
    pin_errors, pin_warnings = audit_pins_and_packs()
    errors = list(source["errors"]) + pin_errors
    warnings = list(source["warnings"]) + pin_warnings
    for row in warnings:
        print(f"WARN {row}")
    if errors:
        print("REBUILD_REQUIRED:")
        for row in errors:
            print(f" - {row}")
        return 2
    print("AUDIT_CLEAN keep a_output_v4 SHA 37a3ba50; v5 reweight SHA 61e83057; do not fetch S5")
    print("CONTINUE_READY copy a_output_v5; init Hub S7 s5best 06354dfc; new Adam; no v3 resume")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
