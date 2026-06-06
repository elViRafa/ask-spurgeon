import shutil
import random
from pathlib import Path

random.seed(42)
corpus_root = Path("data/chspurgeon-sermons")
holdout_dir = Path("data/chspurgeon-holdout")

# Ensure holdout directory exists and is clean
if holdout_dir.exists():
    shutil.rmtree(holdout_dir)
holdout_dir.mkdir(parents=True, exist_ok=True)

# Find all md files
all_files = sorted(list(corpus_root.rglob("*.md")))

if not all_files:
    print("Error: No markdown files found in the corpus.")
    exit(1)

# Sample exactly 50 sermons randomly
holdout_files = random.sample(all_files, min(len(all_files), 50))

print(f"Copying {len(holdout_files)} sermons to holdout directory...")

for src in holdout_files:
    rel = src.relative_to(corpus_root)
    dst = holdout_dir / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  Copied {rel}")

print(f"\nHoldout split complete. Copied {len(holdout_files)} files to {holdout_dir.absolute()}")
print("Original source files remain completely untouched.")
