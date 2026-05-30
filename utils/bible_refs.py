"""
Robust Bible reference extraction and normalization.

Supports:
- Full book names and common abbreviations
- Chapter only: "Romans 8"
- Verse ranges: "John 3:16", "Psalm 23:1-6", "Romans 8:28-30"
- Multiple references in one text
- Case-insensitive matching
- Returns canonical form + structured tuples for filtering

This is intentionally dependency-light (only 'regex').
"""

from __future__ import annotations
import regex as re
from typing import List, Tuple, Set, Optional
from config import BIBLE_BOOKS, BIBLE_ABBREVS


# =============================================================================
# Build lookup structures
# =============================================================================

CANONICAL_BOOKS = {b.lower(): b for b in BIBLE_BOOKS}
CANONICAL_BOOKS.update({b.lower().replace(" ", ""): b for b in BIBLE_BOOKS})

# Reverse map: canonical lower -> original
BOOK_LOOKUP = {}
for canon in BIBLE_BOOKS:
    BOOK_LOOKUP[canon.lower()] = canon
    BOOK_LOOKUP[canon.lower().replace(" ", "")] = canon

for abbrev, canon in BIBLE_ABBREVS.items():
    BOOK_LOOKUP[abbrev.lower()] = canon

# Build a giant alternation for book names/abbrevs (longest first to avoid partial matches)
_sorted_keys = sorted(BOOK_LOOKUP.keys(), key=len, reverse=True)
BOOK_PATTERN = r"(?i)\b(" + "|".join(re.escape(k) for k in _sorted_keys) + r")\b"

# Verse pattern: optional chapter:verse or chapter only, with optional verse range
# Examples matched:
#   Romans 8:28
#   Rom. 8:28-30
#   Psalm 23
#   Ps 23:1-6
#   1 John 3:16
VERSE_PATTERN = re.compile(
    BOOK_PATTERN + r"\.?\s*(\d{1,3})(?::(\d{1,3})(?:\s*[-–—]\s*(\d{1,3}))?)?",
    re.IGNORECASE | re.UNICODE,
)


def normalize_book(book_or_abbrev: str) -> Optional[str]:
    """Return canonical book name or None."""
    key = book_or_abbrev.lower().strip().replace(".", "")
    key = key.replace(" ", "")
    return BOOK_LOOKUP.get(key)


def extract_bible_references(text: str, max_refs: int = 50) -> List[str]:
    """
    Extract and normalize all Bible references found in text.

    Returns list of strings in canonical form:
        "Romans 8:28"
        "Psalm 23:1-6"
        "John 3"
        "Genesis 1:1-5"
    """
    refs: List[str] = []
    seen: Set[str] = set()

    for match in VERSE_PATTERN.finditer(text):
        book_raw = match.group(1)
        chapter = match.group(2)
        verse_start = match.group(3)
        verse_end = match.group(4)

        canon = normalize_book(book_raw)
        if not canon or not chapter:
            continue

        if verse_start:
            if verse_end:
                ref = f"{canon} {chapter}:{verse_start}-{verse_end}"
            else:
                ref = f"{canon} {chapter}:{verse_start}"
        else:
            ref = f"{canon} {chapter}"

        if ref not in seen:
            seen.add(ref)
            refs.append(ref)
            if len(refs) >= max_refs:
                break

    return refs


def extract_primary_scripture(text: str) -> str:
    """
    Heuristic: find the most likely 'primary' scripture of a sermon.

    Strategy:
    1. Look for the first prominent reference near the top (first 1500 chars).
    2. Prefer references that appear in the classic "A SERMON... [text]" header pattern.
    3. Fall back to the very first reference found.
    """
    head = text[:2000]

    # SpurgeonGems / classic header patterns
    header_patterns = [
        r"(?:TEXT|Text|Scripture)[:\s]+([^\n.]+)",
        r"[\"“]([^\"”]+)[\"”][\s\n]+([A-Z][a-z]+\.?\s*\d+[:\d\-]*)",
    ]

    for pat in header_patterns:
        m = re.search(pat, head, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            # Try to find a clean reference in the candidate or next few lines
            refs = extract_bible_references(candidate + " " + head[200:600], max_refs=3)
            if refs:
                return refs[0]

    # Fallback: first reference in the document
    all_refs = extract_bible_references(text, max_refs=5)
    return all_refs[0] if all_refs else ""


def parse_reference(ref: str) -> Optional[Tuple[str, int, Optional[int], Optional[int]]]:
    """
    Parse a normalized reference into (book, chapter, verse_start, verse_end).
    Useful for advanced filtering.
    """
    m = VERSE_PATTERN.match(ref)
    if not m:
        return None
    book = normalize_book(m.group(1))
    chapter = int(m.group(2))
    v1 = int(m.group(3)) if m.group(3) else None
    v2 = int(m.group(4)) if m.group(4) else None
    return book, chapter, v1, v2


def get_bible_book_filter_values() -> List[str]:
    """Return sorted list of canonical books for UI filters."""
    return sorted(BIBLE_BOOKS)


# Convenience: compile a single reference for exact matching in Qdrant filters
def make_reference_filter_expr(book: Optional[str] = None,
                               chapter: Optional[int] = None,
                               verse: Optional[int] = None) -> dict:
    """
    Return a Qdrant filter dict (or LlamaIndex MetadataFilter compatible structure).
    This is used by the app for hybrid filtering.
    """
    # We store "bible_references" as array of strings on each node.
    # For Qdrant we can use "bible_references" "contains" or match any.
    # LlamaIndex will translate MetadataFilters.
    conditions = []
    if book:
        # Match any reference that starts with the book name
        # We will handle this in the app layer with a contains filter on the array.
        pass  # handled specially in app.py
    return {"book": book, "chapter": chapter, "verse": verse}
