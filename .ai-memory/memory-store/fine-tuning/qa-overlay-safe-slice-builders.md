---
store_path: fine-tuning/qa-overlay-safe-slice-builders
title: "Overlay-safe catechism + multi-turn builders"
summary: "| `build_catechism_qa_slice.py` | `--variants`, `--target-new`, `--output` for phrasing variants |"
priority: high
tags: [sft, qa-mix, catechism, multi-turn, builder]
schema_version: 1.3
last_updated: "2026-08-30T22:07:08-04:00"
evidence: [fine_tuning/scripts/build_catechism_qa_slice.py, fine_tuning/scripts/merge_catechism_qa_slice.py, fine_tuning/scripts/build_multiturn_qa_slice.py, fine_tuning/scripts/merge_multiturn_qa_slice.py, fine_tuning/data/qa_mix_manifest.json]
---

# Overlay-safe slice builders — implemented (2026-08-30)

**Status:** Landed. Never used `build_qa_mix_v2.py`.

## What shipped

| Script | Role |
|--------|------|
| `build_catechism_qa_slice.py` | `--variants`, `--target-new`, `--output` for phrasing variants |
| `merge_catechism_qa_slice.py` | `--slice` append-only merge; updates gaps + `catechism_overlays` |
| `build_multiturn_qa_slice.py` | 2-turn rows: bare Q history + CONTEXT follow-up |
| `merge_multiturn_qa_slice.py` | append-only; `multiturn_overlay` in manifest |
| `audit_qa_mix_quality.py` | scores last turn for multiturn; prints multiturn/catechism % |

## Live train after merge

- train **3264** (was 3013)
- catechism **241 (7.4%)** — near F5 ~8%
- multiturn **100 (3.1%)** — inside 2–5%
- refusal ~11.3–11.6%; quote **27.9%**; teacherish 553; caricature 0
- `13_sft_local_readiness` **PASS**; zip repackaged 12.20 MB
- one canonical system prompt on all rows

## Operator notes

- Catechism variants: `qa_catechism_variants.jsonl` (151 added)
- Multiturn: `qa_multiturn_slice.jsonl` (100)
- No GPU / no `build_qa_mix_v2` without operator go
- App `generate_response` is still single-turn today; multiturn trains the `build_chat_messages` shape for when history is wired
