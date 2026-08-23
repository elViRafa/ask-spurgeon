#!/usr/bin/env python3
"""
Fetch public-domain Puritan texts into data/puritans/<author>/.

Every download is **title-verified** (must match expected keywords in the first
bytes) before save — Gutenberg/Archive IDs are frequently wrong.

Usage (repo root):
  python continued_pretrain/scripts/10_fetch_puritans.py
  python continued_pretrain/scripts/10_fetch_puritans.py --only owen,watson
  python continued_pretrain/scripts/10_fetch_puritans.py --list
  python continued_pretrain/scripts/10_fetch_puritans.py --rebuild-mix
"""

from __future__ import annotations

import argparse
import html as html_lib
import re
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path


USER_AGENT = "search-sermons-cpt-puritan-fetcher/1.0 (research; public-domain only)"
# Some Archive.org CDN nodes present expired certs; PD research downloads still OK.
SSL_CTX = ssl._create_unverified_context()


def ia_dl(ident: str, name: str | None = None) -> str:
    """Internet Archive item download URL (prefer over /stream/ which returns HTML shells)."""
    fname = name or f"{ident}_djvu.txt"
    return f"https://archive.org/download/{ident}/{fname}"


# Verified catalog (title-checked downloads as of 2026-07-13). See data/puritans/PROVENANCE.md.
CATALOG: dict[str, dict] = {
    "owen_mortification": {
        "author": "owen",
        "filename": "mortification_of_sin.txt",
        "title": "Of the Mortification of Sin in Believers (Owen)",
        "urls": [ia_dl("ontemptationmort00owenuoft")],
        "must_match": ["owen", "mortification"],
    },
    "owen_indwelling_sin": {
        "author": "owen",
        "filename": "indwelling_sin.txt",
        "title": "The Nature of Indwelling Sin (Owen)",
        "urls": [ia_dl("naturepowerdecei00owen")],
        "must_match": ["owen", "sin"],
    },
    "owen_glory_of_christ": {
        "author": "owen",
        "filename": "glory_of_christ.txt",
        "title": "Meditations on the Glory of Christ (Owen)",
        "urls": [
            ia_dl(
                "bim_eighteenth-century_meditations-and-discours_owen-john_1790",
                "bim_eighteenth-century_meditations-and-discours_owen-john_1790_djvu.txt",
            )
        ],
        "must_match": ["owen", "glory"],
    },
    "owen_communion": {
        "author": "owen",
        "filename": "communion_with_god.txt",
        "title": "Of Communion with God (Owen)",
        "urls": [
            ia_dl(
                "bim_early-english-books-1475-1640_of-communion-with-god-_owen-john-dd_1700",
                "bim_early-english-books-1475-1640_of-communion-with-god-_owen-john-dd_1700_djvu.txt",
            )
        ],
        "must_match": ["communion"],
    },
    "watson_body_of_divinity": {
        "author": "watson",
        "filename": "body_of_divinity.txt",
        "title": "A Body of Practical Divinity (Watson)",
        "urls": [
            ia_dl("bodyofpracticald00wats"),
            "https://archive.org/stream/bodyofpracticald00wats/bodyofpracticald00wats_djvu.txt",
        ],
        "must_match": ["watson", "divinity"],
    },
    "sibbes_bruised_reed": {
        "author": "sibbes",
        "filename": "bruised_reed.txt",
        "title": "The Bruised Reed (Sibbes) — OCR may spell BRVISED",
        "urls": [
            ia_dl(
                "bim_early-english-books-1475-1640_the-bruised-reed-and-smo_sibbes-richard_1630",
                "bim_early-english-books-1475-1640_the-bruised-reed-and-smo_sibbes-richard_1630_djvu.txt",
            )
        ],
        "must_match_any": ["bruised", "brvised", "reed", "flax"],
        "min_chars": 50_000,
    },
    "brooks_precious_remedies": {
        "author": "brooks",
        "filename": "precious_remedies.txt",
        "title": "Precious Remedies Against Satan's Devices (Brooks)",
        "urls": [ia_dl("preciousremedies0000broo")],
        "must_match": ["brooks", "precious"],
    },
    "brooks_complete_works_v3": {
        "author": "brooks",
        "filename": "complete_works_vol3.txt",
        "title": "Complete Works of Thomas Brooks vol. 3",
        "urls": [ia_dl("completeworksoft03broo_0")],
        "must_match": ["brooks"],
    },
    "baxter_saints_rest": {
        "author": "baxter",
        "filename": "saints_everlasting_rest.txt",
        "title": "The Saints' Everlasting Rest (Baxter)",
        "urls": [ia_dl("saintseverlastin1847baxt")],
        "must_match": ["baxter", "rest"],
    },
    "baxter_reformed_pastor": {
        "author": "baxter",
        "filename": "reformed_pastor.txt",
        "title": "The Reformed Pastor (Baxter)",
        "urls": [
            ia_dl("reformedpastor00baxt"),
            "https://archive.org/stream/reformedpastor00baxt/reformedpastor00baxt_djvu.txt",
        ],
        "must_match": ["baxter"],
    },
    "flavel_providence": {
        "author": "flavel",
        "filename": "mystery_of_providence.txt",
        "title": "Divine Conduct / Mystery of Providence (Flavel)",
        "urls": [
            ia_dl("divineconductorm00flav"),
            "https://archive.org/stream/divineconductorm00flav/divineconductorm00flav_djvu.txt",
        ],
        "must_match": ["flavel", "provid"],
    },
    "flavel_keeping_heart": {
        "author": "flavel",
        "filename": "keeping_the_heart.txt",
        "title": "Keeping the Heart (Flavel)",
        "urls": [
            ia_dl("treatiseonkeepin00flav"),
            "https://archive.org/stream/treatiseonkeepin00flav/treatiseonkeepin00flav_djvu.txt",
        ],
        "must_match": ["flavel", "heart"],
    },
    "edwards_affections": {
        "author": "edwards",
        "filename": "religious_affections.txt",
        "title": "Religious Affections (Edwards)",
        "urls": [ia_dl("treatiseonreligi00edwarich")],
        "must_match_any": ["edwards", "edward", "affection"],
        "min_chars": 100_000,
    },
    "gurnall_armour": {
        "author": "gurnall",
        "filename": "christian_in_complete_armour.txt",
        "title": "The Christian in Complete Armour (Gurnall)",
        "urls": [
            ia_dl("christianincom00gurn"),
            "https://archive.org/stream/christianincom00gurn/christianincom00gurn_djvu.txt",
        ],
        "must_match": ["gurnall", "armour"],
    },
    "bunyan_grace_abounding": {
        "author": "bunyan",
        "filename": "grace_abounding.txt",
        "title": "Grace Abounding (Bunyan)",
        "urls": [
            ia_dl("graceaboundingto00buny"),
            "https://archive.org/stream/graceaboundingto00buny/graceaboundingto00buny_djvu.txt",
        ],
        "must_match": ["bunyan", "grace"],
    },
}


def fetch_bytes(url: str, timeout: int = 180) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        print(f"    HTTP {e.code}: {url}")
        return None
    except Exception as e:
        print(f"    fail: {e}")
        return None


def to_text(data: bytes) -> str:
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def strip_html(text: str) -> str:
    if "<html" not in text.lower() and "<body" not in text.lower():
        return text
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_pd_text(text: str) -> str:
    text = strip_html(text)
    # Gutenberg banners
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
    # Archive OCR form feeds
    text = text.replace("\f", "\n\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def verify(text: str, entry: dict) -> bool:
    head = text[:20_000].lower()
    whole = text.lower()
    min_chars = int(entry.get("min_chars") or 1500)
    if len(text) < min_chars:
        return False
    must = entry.get("must_match") or []
    if must and not all(k.lower() in head or k.lower() in whole[:50_000] for k in must):
        return False
    any_keys = entry.get("must_match_any") or []
    if any_keys and not any(k.lower() in head or k.lower() in whole[:50_000] for k in any_keys):
        return False
    return True


def download_entry(repo: Path, key: str, entry: dict, force: bool = False) -> tuple[str, str]:
    """Returns (status, message). status in ok|skip|fail."""
    dest = repo / "data" / "puritans" / entry["author"] / entry["filename"]
    if dest.exists() and dest.stat().st_size > 2000 and not force:
        return "skip", f"exists ({dest.stat().st_size:,} bytes)"

    for url in entry["urls"]:
        print(f"    try {url}")
        data = fetch_bytes(url)
        if not data or len(data) < 1500:
            continue
        text = clean_pd_text(to_text(data))
        if not verify(text, entry):
            print(f"    REJECT title/size check")
            print(f"    head: {text[:180]!r}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        return "ok", f"wrote {dest} ({len(text):,} chars)"

    return "fail", "all URLs failed or rejected"


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Fetch verified PD Puritan texts")
    p.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent.parent))
    p.add_argument("--list", action="store_true")
    p.add_argument("--only", default=None, help="Comma-separated keys or authors")
    p.add_argument("--force", action="store_true", help="Re-download even if file exists")
    p.add_argument("--rebuild-mix", action="store_true", help="Run 07_build_theology_mix after fetch")
    args = p.parse_args(argv)

    if args.list:
        for k, v in CATALOG.items():
            print(f"{k:28s}  {v['author']:10s}  {v['title']}")
        return

    repo = Path(args.repo_root).resolve()
    keys = list(CATALOG.keys())
    if args.only:
        wanted = {x.strip().lower() for x in args.only.split(",") if x.strip()}
        keys = [
            k
            for k, v in CATALOG.items()
            if k in wanted or v["author"] in wanted or k.split("_")[0] in wanted
        ]

    ok = skip = fail = 0
    results: list[str] = []
    for key in keys:
        entry = CATALOG[key]
        print(f"[{key}] {entry['title']}")
        status, msg = download_entry(repo, key, entry, force=args.force)
        print(f"  → {status}: {msg}")
        results.append(f"{status}\t{key}\t{msg}")
        if status == "ok":
            ok += 1
        elif status == "skip":
            skip += 1
        else:
            fail += 1

    print("=" * 60)
    print(f"Done. ok={ok} skip={skip} fail={fail}")

    # Inventory
    root = repo / "data" / "puritans"
    total = 0
    print("\nInventory data/puritans:")
    for path in sorted(root.rglob("*.txt")):
        n = path.stat().st_size
        total += n
        print(f"  {path.relative_to(repo)}  {n:,} bytes")
    print(f"  TOTAL {total:,} bytes ({total/1e6:.1f} MB)")

    log = repo / "continued_pretrain" / "data" / "puritan_fetch_log.txt"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("\n".join(results) + "\n", encoding="utf-8")
    print(f"Log: {log}")

    if args.rebuild_mix:
        import subprocess

        cmd = [
            sys.executable,
            str(repo / "continued_pretrain" / "scripts" / "07_build_theology_mix.py"),
            "--target-spurgeon-share",
            "0.45",
            "--replay-frac",
            "0.0",
        ]
        print("Rebuilding mix:", " ".join(cmd))
        subprocess.check_call(cmd, cwd=str(repo))

    if fail and ok == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
