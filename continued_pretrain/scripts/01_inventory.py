import os
from pathlib import Path

corpus_root = Path("data/chspurgeon-sermons")

if not corpus_root.exists():
    print(f"Error: Corpus root not found at {corpus_root.absolute()}")
    exit(1)

# List all directories that match volume-X
volumes = sorted(
    [d for d in corpus_root.iterdir() if d.is_dir() and d.name.startswith("volume-")],
    key=lambda x: int(x.name.split("-")[1])
)

total_files = 0
total_chars = 0

print(f"| {'Volume':<20} | {'Files':>6} | {'Avg Size (chars)':>18} |")
print(f"|:{'-'*20}-|:{'-'*6}-|:{'-'*18}-|")

for vol in volumes:
    md_files = sorted(vol.glob("*.md"))
    chars = 0
    for f in md_files:
        try:
            chars += len(f.read_text(encoding="utf-8", errors="replace"))
        except Exception as e:
            print(f"Error reading {f}: {e}")
    avg = chars // len(md_files) if md_files else 0
    total_files += len(md_files)
    total_chars += chars
    print(f"| {vol.name:<20} | {len(md_files):>6} | {avg:>13,} chars |")

print(f"|:{'-'*20}-|:{'-'*6}-|:{'-'*18}-|")
print(f"| {'TOTAL':<20} | {total_files:>6} | {total_chars // total_files if total_files else 0:>13,} chars |")
print(f"\nEstimated total size: {total_chars / 1e6:.2f} MB ({total_chars:,} characters)")
