# Phase 1: Spurgeon Continued Pretraining — Step 2: Data Cleaning & Preparation Report

This file documents the results, metrics, and pipeline details for **Step 2: Data Cleaning & Preparation** of the continued pretraining phase.

---

## 1. Cleaned Dataset Metrics

We successfully executed the cleaned corpus builder script on the raw Markdown sermons (skipping the 50-sermon holdout set) and computed the tokenization projections using the `Qwen/Qwen2.5-3B` tokenizer:

| Metric | Training Corpus (`spurgeon_train.txt`) | Holdout Corpus (`spurgeon_holdout.txt`) |
| :--- | :--- | :--- |
| **Sermons Processed** | 3,486 sermons | 50 sermons |
| **Skipped / Deduplicated** | 51 files (stubs, duplicates) | 0 files |
| **Total Characters** | 127,584,192 characters | 1,829,882 characters |
| **File Size (MB)** | 121.67 MB | 1.75 MB |
| **Estimated Tokens** | **30,284,659 tokens** | **434,250 tokens** |
| **Token-to-Char Ratio** | 0.2374 | 0.2374 |
| **Doc Separators (`<\|endoftext\|>`)**| 3,486 occurrences | 50 occurrences |

*All metrics are verified locally using Qwen's official tokenizer.*

---

## 2. Cleaning Pipeline Implementation

The cleaning pass was performed by the newly created Python script [05_build_corpus.py](file:///c:/Users/rafael/Projetos/search-sermons/continued_pretrain/scripts/05_build_corpus.py). The pipeline processed raw markdown text through the following sequence:

1. **Line Ending Normalization:** Converted Windows line endings (`\r\n`) to standard Unix line endings (`\n`).
2. **HTML Entity Decoding:** Handled XML/HTML entity noise (e.g., converting `&mdash;` to `—`, `&amp;` to `&`) to restore clean typographic flow before tag removal.
3. **Targeted Footer Truncation:** Scanned the last 25 lines of each file to locate publisher ads, hymn lists, scripture reading references, and collection credit blocks (e.g. references to Passmore & Alabaster, collection version credits, or scripture read portions). When found, the text was truncated immediately before that line.
4. **Header Stripping:** Removed Markdown heading markers (`#`, `##`, etc.) but preserved the text content.
5. **Emphasis Stripping:** Removed bold/italic characters (`*`, `_`, `**`, `___`) to keep text clean.
6. **Blockquote Cleanout:** Stripped the `>` prefix at the start of blockquote lines.
7. **Rule Removal:** Stripped horizontal rules (`---`, `***`).
8. **Link Unwrapping:** Extracted text from markdown links `[display text](url)` and discarded the URL.
9. **Footnote Cleanout:** Stripped footnote markers (`[^1]`) and definitions (`[^1]: ...`).
10. **HTML Cleanout:** Removed raw HTML tags (e.g. `<p>`, `<br>`).
11. **Numbering Cleanup:** Removed isolated sermon and volume lines (e.g. `Volume LII.`, `Sermon No. 1234`).
12. **Paragraph Consolidation:** Collapsed 3+ consecutive blank lines down to 2 to maintain consistent spacing between paragraphs.

---

## 3. Key Bug Fix: Tightening Truncation Logic

During manual sanity checks and validation of the holdout split, we identified a critical false positive issue:
* **Symptom:** In `volume-35\sermon_2115.md`, the cleaning script cut off the last 20 lines of the sermon.
* **Root Cause:** The script's `footer_patterns` list included the pattern `re.compile(r"pray\s+the\s+holy\s+spirit", re.I)`. In the last 25 lines of this sermon, Spurgeon had spoken: *"I pray the Holy Spirit to bring you to decision..."*. The case-insensitive regex triggered on this line, misidentifying it as an editorial footer note and truncating the sermon early.
* **Scope:** A scan of the entire raw corpus revealed **48 sermons** containing mixed-case/lowercase `pray the holy spirit` phrases in their last 25 lines, causing them to be truncated prematurely.
* **Mitigation:** We tightened the pattern to `re.compile(r"pray\s+the\s+holy\s+spirit\s+will\s+use", re.I)` to specifically match the uppercase editorial footer string: `PRAY THE HOLY SPIRIT WILL USE THIS SERMON TO BRING MANY...`.
* **Result:** Retrying the scan with the new pattern confirmed **zero false positive matches** on normal sermon text, while successfully cleaning the 26 files that possessed the actual editorial footer. This recovered **~89,000 characters (over 21,000 tokens)** of actual sermon text that would have otherwise been lost.

---

## 4. How to Verify Local Output

Both datasets are output in the dedicated folder:
* **Training set:** `continued_pretrain/data/spurgeon_train.txt` (ignored by Git)
* **Holdout set:** `continued_pretrain/data/spurgeon_holdout.txt` (ignored by Git)

You can run the token verification script [06_verify_tokens.py](file:///c:/Users/rafael/Projetos/search-sermons/continued_pretrain/scripts/06_verify_tokens.py) locally to output the finalized metrics:
```bash
.venv/Scripts/python continued_pretrain/scripts/06_verify_tokens.py
```
