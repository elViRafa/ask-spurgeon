---
store_path: failures/pack-document-isolated-spliced-ead647ad1d
title: "pack_document_isolated spliced leftover tokens of a document longer than max_seq"
summary: "pack_document_isolated spliced leftover tokens of a document longer than max_seq_len onto the start of the next short document (same row), recreating stream-pack leftover-A + start-of-B"
priority: medium
tags: [cpt, failure, fix, packing, unsloth]
schema_version: 1.3
last_updated: "2026-08-26T08:47:44-04:00"
occurrences: 1
error_signature: "pack_document_isolated spliced leftover tokens of a document longer than max_seq_len onto the start of the next short document (same row), recreating stream-pack leftover-a + start-of-b"
---

## Occurrence 1 — 2026-08-26T08:47:44-04:00

**Error:**
pack_document_isolated spliced leftover tokens of a document longer than max_seq_len onto the start of the next short document (same row), recreating stream-pack leftover-A + start-of-B

**Fix:**
Flush every split-doc window as its own row so only complete documents that both fit share a row. Added test_long_doc_leftover_not_spliced_onto_next. DataCollatorForSeq2Seq preserves post-EOS labels=-100.
