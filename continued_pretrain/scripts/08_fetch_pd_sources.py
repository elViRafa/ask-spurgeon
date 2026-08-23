#!/usr/bin/env python3
"""
Fetch public-domain theology sources for CPT v2 into data/{puritans,confessions,bible}.

Sources are Project Gutenberg plain-text mirrors (public domain). Spot-check OCR/quality
after download. Held-out Heidelberg + Belgic go under continued_pretrain/data/holdouts_manual/
and are NEVER placed under training dirs.

Usage (from repo root):
  python continued_pretrain/scripts/08_fetch_pd_sources.py
  python continued_pretrain/scripts/08_fetch_pd_sources.py --only bunyan,kjv,wsc
  python continued_pretrain/scripts/08_fetch_pd_sources.py --list
"""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
from pathlib import Path


# Gutenberg UTF-8 plain text URLs (stable-ish mirrors). IDs are PD classics.
CATALOG: dict[str, dict] = {
    # Puritans / classic Reformed literature
    "bunyan_pilgrim": {
        "bucket": "puritans/bunyan",
        "filename": "pilgrims_progress.txt",
        "url": "https://www.gutenberg.org/files/131/131-0.txt",
        "title": "The Pilgrim's Progress (Bunyan)",
    },
    "bunyan_holy_war": {
        "bucket": "puritans/bunyan",
        "filename": "the_holy_war.txt",
        "url": "https://www.gutenberg.org/files/395/395-0.txt",
        "title": "The Holy War (Bunyan) — verify title after download",
    },
    "bunyan_badman": {
        "bucket": "puritans/bunyan",
        "filename": "life_and_death_of_mr_badman.txt",
        "url": "https://www.gutenberg.org/files/1986/1986-0.txt",
        "title": "Life and Death of Mr Badman (Bunyan)",
    },
    # Bible
    "kjv": {
        "bucket": "bible/kjv",
        "filename": "kjv.txt",
        "url": "https://www.gutenberg.org/files/10/10-0.txt",
        "title": "King James Bible",
    },
}
# Note: WSC + Heidelberg are curated under data/confessions and holdouts_manual
# (Gutenberg IDs for those titles are often mis-matched; do not auto-fetch blindly).
# Add more Puritans via CCEL / Archive.org manually — always spot-check the title line.


USER_AGENT = "search-sermons-cpt-fetcher/1.0 (+local research; public-domain only)"


def download(url: str, dest: Path, timeout: int = 120) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1000:
        print(f"  skip (exists): {dest} ({dest.stat().st_size:,} bytes)")
        return True
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} for {url}")
        return False
    except Exception as e:
        print(f"  failed: {e}")
        return False
    if len(data) < 500:
        print(f"  too small ({len(data)} bytes), skipping write")
        return False
    dest.write_bytes(data)
    print(f"  wrote {dest} ({len(data):,} bytes)")
    return True


def resolve_dest(repo: Path, entry: dict) -> Path:
    if entry.get("holdout"):
        return repo / "continued_pretrain" / "data" / "holdouts_manual" / entry["filename"]
    return repo / "data" / entry["bucket"] / entry["filename"]


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Fetch PD theology sources for CPT")
    p.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent.parent))
    p.add_argument("--list", action="store_true", help="List catalog and exit")
    p.add_argument(
        "--only",
        default=None,
        help="Comma-separated catalog keys (default: all non-holdout + heidelberg holdout)",
    )
    p.add_argument("--include-holdouts", action="store_true", help="Also fetch manual holdouts")
    args = p.parse_args(argv)

    if args.list:
        for k, v in CATALOG.items():
            tag = " [HOLDOUT]" if v.get("holdout") else ""
            print(f"{k:24s}  {v['bucket']:28s}  {v['title']}{tag}")
        return

    repo = Path(args.repo_root).resolve()
    if args.only:
        keys = [k.strip() for k in args.only.split(",") if k.strip()]
    else:
        keys = [
            k
            for k, v in CATALOG.items()
            if (not v.get("holdout")) or args.include_holdouts
        ]

    ok, fail = 0, 0
    for key in keys:
        if key not in CATALOG:
            print(f"Unknown key: {key}")
            fail += 1
            continue
        entry = CATALOG[key]
        dest = resolve_dest(repo, entry)
        print(f"[{key}] {entry['title']}")
        print(f"  → {dest}")
        if download(entry["url"], dest):
            ok += 1
        else:
            fail += 1

    print("=" * 50)
    print(f"Done. ok={ok} fail={fail}")
    print("Next:")
    print("  python continued_pretrain/scripts/07_build_theology_mix.py")
    print("  python continued_pretrain/scripts/06_verify_tokens.py --mix")
    if fail:
        print("Some URLs may have moved — fall back to CCEL / Archive.org (see SOURCES_SOTA_CPT.md).")
        sys.exit(1)


if __name__ == "__main__":
    main()
