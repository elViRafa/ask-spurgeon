import re
import html
from pathlib import Path

def clean_md_sermon(raw_text: str) -> str:
    # 1. Normalise Windows line endings first
    text = raw_text.replace('\r\n', '\n')

    # 2. Decode HTML entities (&mdash; → —, &amp; → &, &lt; → <, etc.)
    text = html.unescape(text)

    # 3. Truncate footer metadata at the end of the file
    # We look at the last 25 lines of the file for the start of the footer
    # to avoid falsely matching keywords (like "alabaster") inside the sermon body.
    lines = text.splitlines()
    total_lines = len(lines)
    scan_start = max(0, total_lines - 25)
    truncate_idx = None

    footer_patterns = [
        re.compile(r"portion\s+of\s+scripture\s+read", re.I),
        re.compile(r"portions\s+of\s+scripture\s+read", re.I),
        re.compile(r"hymns\s+from", re.I),
        re.compile(r"pray\s+the\s+holy\s+spirit\s+will\s+use", re.I),
        re.compile(r"adapted\s+from\s+the\s+c\.\s*h\.\s*spurgeon\s+collection", re.I),
        re.compile(r"the\s+tongue\s+of\s+the\s+wicked\s+has\s+assailed", re.I),
        re.compile(r"passmore\s*&\s*alabaster", re.I),
        re.compile(r"published\s+by\s+passmore", re.I),
        re.compile(r"london:\s+passmore", re.I),
    ]

    for i in range(scan_start, total_lines):
        line = lines[i]
        matched = False
        for pattern in footer_patterns:
            if pattern.search(line):
                matched = True
                break
        if matched:
            truncate_idx = i
            break

    if truncate_idx is not None:
        lines = lines[:truncate_idx]
        text = '\n'.join(lines)

    # 4. Strip heading markers, keep text
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # 5. Strip bold/italic emphasis markers
    text = re.sub(r'\*{1,3}(.+?)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}(.+?)_{1,3}', r'\1', text)

    # 6. Strip blockquote markers, keep text
    text = re.sub(r'^>\s?', '', text, flags=re.MULTILINE)

    # 7. Remove horizontal rules
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)

    # 8. Remove markdown links — keep display text
    text = re.sub(r'\[(.+?)\]\(.*?\)', r'\1', text)

    # 9. Remove footnote references: [^1] or [^note]
    text = re.sub(r'\[\^[^\]]+\]', '', text)

    # 10. Remove footnote definitions: [^1]: ...
    text = re.sub(r'^\[\^[^\]]+\]:.*$', '', text, flags=re.MULTILINE)

    # 11. Remove remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # 12. Remove sermon/volume number lines
    text = re.sub(r'^(SERMON\s+)?NO\.\s*\d+\.?\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'^Volume\s+[IVXLCDM\d]+\.?\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)

    # 13. Collapse 3+ blank lines to one (i.e. double newline for one blank line)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

def build_corpus(corpus_root: str, output_file: str, holdout_dir: str = None):
    root = Path(corpus_root).resolve()
    holdout_path = Path(holdout_dir).resolve() if holdout_dir else None
    seen = set()
    written, skipped = 0, 0

    # Ensure parent directory of output exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as out:
        for md_file in sorted(root.rglob("*.md")):
            if md_file.name.lower() == 'readme.md':
                skipped += 1
                continue

            # If holdout_dir is provided, check if this file is a holdout and skip it
            if holdout_path:
                rel = md_file.resolve().relative_to(root)
                if (holdout_path / rel).exists():
                    skipped += 1
                    continue

            raw = md_file.read_text(encoding='utf-8', errors='replace')

            # Dedup by first 300 chars of raw content
            fingerprint = raw[:300].strip()
            if fingerprint in seen:
                skipped += 1
                continue
            seen.add(fingerprint)

            cleaned = clean_md_sermon(raw)

            if len(cleaned) < 500:  # skip stubs and index files
                skipped += 1
                continue

            out.write(cleaned)
            out.write('\n<|endoftext|>\n\n')
            written += 1

    print(f"Written: {written} sermons to {output_file} | Skipped/deduped: {skipped}")

if __name__ == "__main__":
    # Define paths relative to workspace root
    base_dir = Path(__file__).resolve().parent.parent.parent
    corpus_root = base_dir / "data" / "chspurgeon-sermons"
    holdout_dir = base_dir / "data" / "chspurgeon-holdout"
    train_output = base_dir / "continued_pretrain" / "data" / "spurgeon_train.txt"
    holdout_output = base_dir / "continued_pretrain" / "data" / "spurgeon_holdout.txt"

    print("Building training corpus (skipping holdout)...")
    build_corpus(
        corpus_root=corpus_root,
        output_file=train_output,
        holdout_dir=holdout_dir
    )

    print("\nBuilding holdout corpus...")
    build_corpus(
        corpus_root=holdout_dir,
        output_file=holdout_output
    )
