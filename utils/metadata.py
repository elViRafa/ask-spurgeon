"""
Metadata extraction for different sermon sources.

Supports:
1. lyteword Markdown format (recommended)
2. spurgeongems.org chs*.pdf files (classic layout)
3. Future: other collections
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Dict, Any
from config import DEFAULT_AUTHOR
from utils.bible_refs import extract_bible_references, extract_primary_scripture


# =============================================================================
# Markdown (lyteword/chspurgeon-sermons) parser
# =============================================================================

def parse_markdown_sermon(path: Path) -> Dict[str, Any]:
    """
    Parse a sermon-*.md file from the lyteword collection.

    Expected header:
        # Sermon 42 | The Title of the Sermon

        > Scripture quote...
        > Reference

    Returns a dict ready for SermonMetadata + full text.
    """
    text = path.read_text(encoding="utf-8", errors="ignore")

    # Title line: supports "Sermon 42 | Title", "Sermon 39 & 40 | Title", "Sermon 39-40 | Title"
    title_match = re.search(
        r"^#\s*Sermon\s+(\d+)(?:\s*[&\-–—]\s*\d+)?\s*\|\s*(.+?)\s*$",
        text,
        re.MULTILINE | re.IGNORECASE,
    )
    sermon_number = int(title_match.group(1)) if title_match else None
    title = title_match.group(2).strip() if title_match else path.stem

    # Try to find volume from path or frontmatter
    volume = None
    vol_match = re.search(r"volume-(\d+)", str(path))
    if vol_match:
        volume = int(vol_match.group(1))

    # Primary scripture (usually right after title)
    primary = extract_primary_scripture(text[:3000]) or ""
    refs = extract_bible_references(text)

    # Year heuristic (many files don't have it; we can enrich later)
    year = None
    year_match = re.search(r"\b(18[5-9]\d|189[0-2])\b", text[:1500])
    if year_match:
        year = int(year_match.group(1))

    # Source URL (we can construct spurgeongems style if we want)
    source_url = f"https://www.spurgeongems.org/sermon/chs{sermon_number}.pdf" if sermon_number else ""

    return {
        "author": DEFAULT_AUTHOR,
        "sermon_number": sermon_number,
        "title": title,
        "volume": volume,
        "year": year,
        "primary_scripture": primary,
        "bible_book": primary.split()[0] if primary else "",
        "source_url": source_url,
        "bible_references": refs,
        "full_text": text,
    }


# =============================================================================
# PDF (spurgeongems chsN.pdf) parser
# =============================================================================

def parse_pdf_sermon_text(text: str, filename: str) -> Dict[str, Any]:
    """
    Parse raw extracted text from a chs*.pdf.

    These PDFs have a very consistent structure:
    - First lines contain sermon number + title
    - "A SERMON DELIVERED ON SABBATH MORNING, [DATE], BY THE REV. C. H. SPURGEON..."
    - Scripture block
    """
    # Sermon number from filename chs123.pdf
    num_match = re.search(r"chs(\d+)", filename.lower())
    sermon_number = int(num_match.group(1)) if num_match else None

    # Title: usually early, often ALL CAPS or after sermon number
    title = "Untitled Sermon"
    title_match = re.search(
        r"(?:^|\n)\s*(?:Sermon\s*#?\s*\d+\s*)?([A-Z][A-Z\s\-:,'’]+?)(?:\n|NO\.|\d{1,4})",
        text[:1500],
        re.IGNORECASE,
    )
    if title_match:
        candidate = title_match.group(1).strip()
        if len(candidate) > 8 and len(candidate) < 120:
            title = candidate.title()

    # Date + preacher line
    year = None
    date_match = re.search(
        r"DELIVERED ON [A-Z ]+,?\s*([A-Z][a-z]+)\s+(\d{1,2}),?\s*(18\d{2})",
        text[:2000],
    )
    if date_match:
        year = int(date_match.group(3))

    # Primary scripture
    primary = extract_primary_scripture(text[:2500]) or ""
    refs = extract_bible_references(text)

    # Volume is hard from single PDF; we leave it None or infer from sermon ranges later
    volume = None

    return {
        "author": DEFAULT_AUTHOR,
        "sermon_number": sermon_number,
        "title": title,
        "volume": volume,
        "year": year,
        "primary_scripture": primary,
        "bible_book": primary.split()[0] if primary else "",
        "source_url": f"https://www.spurgeongems.org/sermon/{filename}",
        "bible_references": refs,
        "full_text": text,
    }


# =============================================================================
# Generic dispatcher
# =============================================================================

def extract_metadata_from_file(path: Path) -> Dict[str, Any]:
    """Route to the correct parser based on extension."""
    if path.suffix.lower() == ".md":
        return parse_markdown_sermon(path)
    elif path.suffix.lower() == ".pdf":
        # Caller must pass already-extracted text for PDFs
        raise ValueError("For PDFs, extract text first then call parse_pdf_sermon_text")
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")
