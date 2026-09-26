#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import audit_cpt_mix_sources as audit  # noqa: E402


def test_locked_shas() -> None:
    assert audit.EXPECT_MIX_V5.startswith("61e83057")
    assert audit.EXPECT_MIX_V4.startswith("37a3ba50")
    assert audit.EXPECT_MIX_V3.startswith("23dd3820")
    assert len(audit.NEW_AUTHOR_FILES) == 11


def test_clean_md_sermon_maps_glyphs() -> None:
    spec = importlib.util.spec_from_file_location(
        "corpus05", SCRIPTS / "05_build_corpus.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cleaned = mod.clean_md_sermon("A \u017fermon \u25a0 end")
    assert "\u017f" not in cleaned
    assert "\u25a0" not in cleaned
    assert "sermon" in cleaned.lower()


def main() -> None:
    test_locked_shas()
    test_clean_md_sermon_maps_glyphs()
    print("PASS: locked SHAs")
    print("PASS: Spurgeon cleaner maps glyphs")


if __name__ == "__main__":
    main()
