---
store_path: fine-tuning/sft-qa-mix-v2
title: "SFT QA mix v2 (serve-shaped)"
summary: "**Status:** Built locally, no GPU"
priority: high
tags: [sft, qa-mix, f3, f5]
schema_version: 1.3
last_updated: "2026-08-28T20:41:31-04:00"
evidence: [fine_tuning/scripts/build_qa_mix_v2.py, fine_tuning/data/qa_mix_manifest.json, "config.py:57", "utils/prompts.py:60"]
---

# SFT QA mix v2 — serve-shaped (2026-08-28)

**Status:** Built locally, no GPU. `13_sft_local_readiness.py` PASS. Do not start Runpod/Kaggle training until operator decides.

## Counts

| Split | Rows |
|-------|------|
| train | 2923 |
| val | 153 |
| test frozen | 100 (50 answerable / 50 refusal) |

- Train refusal: **347 (11.9%)** — inside 10–15% F5 target (v1 was 14 / 0.5%).
- Sermon match rate: **99.9%** (2755/2757) against `data/chspurgeon-sermons` (3536 files).
- k histogram (weighted toward serve k=4): 1=136, 3=408, 4=1968, 5=275.

## Serve contract encoded in examples

- System: `config.SPURGEON_SFT_SYSTEM_PROMPT`
- Headers: `[Sermon N — "Title", Volume V | Text: ref]` (`utils.prompts.format_context`)
- User wrapper: `CONTEXT (excerpts...)` + headed chunks + `QUESTION:`
- Default k=4 (`FINE_TUNED_SIMILARITY_TOP_K`); chunking ~2800 chars / 450 overlap as a 768/128 token proxy
- Fidelity: original answers kept; light trailing `[Sermon N]` citation when matched
- Refusals: original ~30 + 389 synthesized (real questions + unrelated chunks, plus anachronism prompts)

## Builder / package

- `fine_tuning/scripts/build_qa_mix_v2.py` → jsonl + `qa_mix_manifest.json` version `qa_mix_v2`
- `12_package_kaggle_qa_mix.py` → `fine_tuning/data/kaggle_upload/spurgeon-qa-mix-v1.zip` (11.75 MB; Kaggle dataset name unchanged)
- D_sota tokenizer: `AutoTokenizer.from_pretrained` (not `FastLanguageModel.get_tokenizer`)

## Remaining F5 gaps

- No new 5–6k teacher-generated set (rewrapped existing 2787)
- No catechism/confession slice (~8%)
- No multi-turn examples
- Chunking is char-approx, not LlamaIndex `SentenceSplitter`
- Citations are trailing `[Sermon N]`, not teacher-written inline quotes
