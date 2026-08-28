#!/usr/bin/env python3
"""
Build continued_pretrain/data/replay/general_replay.txt from Project Gutenberg PD classics.

Used as anti-forgetting general English in the theology CPT mix (~10% share).
"""
from __future__ import annotations

import argparse
import re
import ssl
import urllib.error
import urllib.request
from pathlib import Path

USER_AGENT = "search-sermons-cpt-replay/1.0 (research; public-domain only)"
SSL_CTX = ssl._create_unverified_context()
DOC_SEP = "<|endoftext|>"

# Title-verified Gutenberg plain-text IDs (literature, not theology).
CATALOG: list[tuple[str, str, str]] = [
    ("1342", "pride_and_prejudice.txt", "Pride and Prejudice"),
    ("11", "alice_wonderland.txt", "Alice in Wonderland"),
    ("84", "frankenstein.txt", "Frankenstein"),
    ("98", "tale_of_two_cities.txt", "A Tale of Two Cities"),
    ("1661", "sherlock_holmes.txt", "Adventures of Sherlock Holmes"),
    ("2701", "moby_dick.txt", "Moby Dick"),
    ("345", "dracula.txt", "Dracula"),
    ("76", "huckleberry_finn.txt", "Huckleberry Finn"),
    ("174", "dorian_gray.txt", "Picture of Dorian Gray"),
    ("1260", "jane_eyre.txt", "Jane Eyre"),
    ("1400", "great_expectations.txt", "Great Expectations"),
    ("25344", "scarlet_letter.txt", "The Scarlet Letter"),
    ("219", "heart_of_darkness.txt", "Heart of Darkness"),
    ("43", "jekyll_hyde.txt", "Dr Jekyll and Mr Hyde"),
    ("2591", "grimms_fairy_tales.txt", "Grimm's Fairy Tales"),
    ("16", "peter_pan.txt", "Peter Pan"),
    ("55", "wizard_of_oz.txt", "Wonderful Wizard of Oz"),
    ("1184", "count_of_monte_cristo.txt", "Count of Monte Cristo"),
    ("1232", "the_prince.txt", "The Prince (Machiavelli)"),
    ("1497", "republic.txt", "The Republic (Plato)"),
    ("1998", "troilus_cressida.txt", "Troilus and Cressida"),
    ("205", "walden.txt", "Walden"),
    ("514", "little_women.txt", "Little Women"),
    ("2600", "war_and_peace.txt", "War and Peace"),
]


def fetch(gid: str) -> str | None:
    urls = [
        f"https://www.gutenberg.org/files/{gid}/{gid}-0.txt",
        f"https://www.gutenberg.org/files/{gid}/{gid}.txt",
        f"https://www.gutenberg.org/ebooks/{gid}.txt.utf-8",
    ]
    for url in urls:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=120, context=SSL_CTX) as resp:
                data = resp.read()
        except Exception as e:
            print(f"    fail {url}: {e}")
            continue
        if len(data) < 5000:
            continue
        for enc in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                return data.decode(enc)
            except UnicodeDecodeError:
                continue
        return data.decode("utf-8", errors="replace")
    return None


def strip_gutenberg(text: str) -> str:
    m = re.search(
        r"\*\*\*\s*START OF (THIS|THE) PROJECT GUTENBERG EBOOK.*?\*\*\*",
        text,
        re.I | re.S,
    )
    if m:
        text = text[m.end() :]
    m = re.search(
        r"\*\*\*\s*END OF (THIS|THE) PROJECT GUTENBERG EBOOK.*?\*\*\*",
        text,
        re.I | re.S,
    )
    if m:
        text = text[: m.start()]
    return text.strip()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent.parent))
    args = p.parse_args()
    repo = Path(args.repo_root)
    out_dir = repo / "continued_pretrain" / "data" / "replay"
    out_dir.mkdir(parents=True, exist_ok=True)
    parts: list[str] = []
    ok = 0
    for gid, fname, title in CATALOG:
        print(f"[{gid}] {title}")
        dest = out_dir / fname
        if dest.exists() and dest.stat().st_size > 5000:
            text = dest.read_text(encoding="utf-8", errors="replace")
            print(f"  skip exists ({len(text):,} chars)")
        else:
            raw = fetch(gid)
            if not raw:
                print("  FAIL download")
                continue
            text = strip_gutenberg(raw)
            # Title sanity: reject if Gutenberg redirected to wrong book (too short after strip)
            if len(text) < 20_000:
                print(f"  REJECT too short after strip ({len(text)})")
                continue
            dest.write_text(text, encoding="utf-8")
            print(f"  wrote {dest.name} ({len(text):,} chars)")
        parts.append(text)
        ok += 1

    concat = (DOC_SEP + "\n").join(parts)
    out = out_dir / "general_replay.txt"
    out.write_text(concat, encoding="utf-8")
    print("=" * 60)
    print(f"Books ok={ok}/{len(CATALOG)}")
    print(f"Wrote {out} ({len(concat):,} chars)")


if __name__ == "__main__":
    main()
