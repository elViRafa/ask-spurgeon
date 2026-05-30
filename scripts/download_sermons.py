#!/usr/bin/env python3
"""
Optional helper: Download a small number of Spurgeon PDFs for testing.

Usage:
    python scripts/download_sermons.py --count 20 --start 1

Note: For production, strongly prefer the Markdown edition:
    git clone https://github.com/lyteword/chspurgeon-sermons.git data/chspurgeon-sermons
"""

import argparse
import time
from pathlib import Path
import requests
from tqdm import tqdm

BASE_URL = "https://www.spurgeongems.org/sermon/chs{num}.pdf"
DEFAULT_DIR = Path("data/sermons")


def download_sermons(start: int = 1, count: int = 10, out_dir: Path = DEFAULT_DIR):
    out_dir.mkdir(parents=True, exist_ok=True)

    for i in tqdm(range(start, start + count), desc="Downloading PDFs"):
        url = BASE_URL.format(num=i)
        dest = out_dir / f"chs{i}.pdf"
        if dest.exists():
            continue
        try:
            r = requests.get(url, timeout=30, stream=True)
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            time.sleep(0.3)  # be polite
        except Exception as e:
            print(f"Failed to download chs{i}.pdf: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--out", type=str, default=str(DEFAULT_DIR))
    args = parser.parse_args()

    download_sermons(args.start, args.count, Path(args.out))
    print("Done. Consider using the Markdown source for best results.")
