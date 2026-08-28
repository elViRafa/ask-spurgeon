---
store_path: failures/unicodeencodeerror-val-codec-can-896018dfa4
title: "UnicodeEncodeError: 'charmap' codec can't encode character '\\u2192' in position "
summary: "UnicodeEncodeError: 'charmap' codec can't encode character '\\u2192' in position 2 (Windows cp1252 console) when 10_fetch_puritans.py printed status arrows"
priority: medium
tags: [cpt, encoding, failure, fix, mix, windows]
schema_version: 1.3
last_updated: "2026-08-27T15:23:32-04:00"
occurrences: 2
error_signature: "unicodeencodeerror: <val> codec can<val><path>' in position <n> (windows cp<n> console) when <n>_fetch_puritans.py printed status arrows."
failure_key: unicodeencodeerror
---

## Occurrence 1 — 2026-08-27T11:02:21-04:00

**Error:**
UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' in position 2 (Windows cp1252 console) when 10_fetch_puritans.py printed status arrows.

**Fix:**
Replaced the Unicode arrow in the status print with ASCII '->'. Also set PYTHONIOENCODING=utf-8. Fetch had already written Owen Goold vol.1 before the crash; resume skipped that file.

## Occurrence 2 — 2026-08-27T15:23:32-04:00

UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' in position 23 (Windows cp1252 console) when 07_build_theology_mix.py printed Paragraph dedup docs_in → docs_out

Replaced Unicode arrows in 07_build_theology_mix.py prints (paragraph dedup and bucket cap) with ASCII '->'. Re-run mix with PYTHONIOENCODING=utf-8. Same class of bug as the fetcher status-arrow crash.
