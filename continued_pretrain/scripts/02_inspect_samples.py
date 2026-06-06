import random
from pathlib import Path

corpus_root = Path("data/chspurgeon-sermons")
all_files = list(corpus_root.rglob("*.md"))

if not all_files:
    print("Error: No markdown files found in the corpus.")
    exit(1)

# Sort files to ensure seed reproducibility across runs
all_files.sort()

random.seed(42)
samples = random.sample(all_files, min(len(all_files), 5))

for path in samples:
    print(f"\n{'='*80}")
    print(f"FILE: {path.relative_to(corpus_root)}")
    print(f"{'='*80}")
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in lines[:60]:
            print(line)
    except Exception as e:
        print(f"Error reading file: {e}")
