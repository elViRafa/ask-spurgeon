from pathlib import Path

corpus_root = Path("data/chspurgeon-sermons")
short_files = []
large_files = []

for path in corpus_root.rglob("*.md"):
    try:
        size = len(path.read_text(encoding="utf-8", errors="replace"))
        rel_path = path.relative_to(corpus_root)
        if size < 3000:
            short_files.append((rel_path, size))
        elif size > 80000:
            large_files.append((rel_path, size))
    except Exception as e:
        print(f"Error reading {path}: {e}")

# Sort short files ascending, large files descending
short_files.sort(key=lambda x: x[1])
large_files.sort(key=lambda x: -x[1])

print(f"=== Found {len(short_files)} short files (< 3,000 chars - stubs/index pages) ===")
for rel_path, size in short_files:
    print(f"  {size:>6,} chars  {rel_path}")

print(f"\n=== Found {len(large_files)} oversized files (> 80,000 chars - possible multi-sermon) ===")
for rel_path, size in large_files:
    print(f"  {size:>6,} chars  {rel_path}")
