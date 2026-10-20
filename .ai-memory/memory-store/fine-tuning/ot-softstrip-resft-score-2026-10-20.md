---
store_path: fine-tuning/ot-softstrip-resft-score-2026-10-20
title: "OT soft-strip re-SFT re-score still weak"
summary: "**Go completed.** Soft-strip + honesty (53) + weighted Unsloth re-SFT → OT re-score under `open_theology_chat_corpus_v1`"
priority: high
tags: [sft, open-theology, eval, soft-strip]
schema_version: 1.3
last_updated: "2026-10-20T12:51:33-03:00"
---

# OT soft-strip re-SFT re-score (2026-10-20)

**Go completed.** Soft-strip + honesty (53) + weighted Unsloth re-SFT → OT re-score under `open_theology_chat_corpus_v1`.

## Adapter

- SHA256: `a34d288652b52b840b1a40bdb5173d49348010830ceab026dc06949478cc49c0`
- Train: 520 steps / 2 epochs; train_loss 0.9975; ~12 s/it; mix 4151 (RAG 3264 + OT 887)
- `SFT_EXPORT=0`; no Hub

## Eval ops

- Pod: Secure 4090 `cjzlpbsvzl4fjc` @ $0.89/hr; destroyed (`POD_DELETED`)
- Report: `fine_tuning/eval_results/open_theology_eval_s8_weighted.json` schema `open_theology_eval_1.1`
- Judge: Gemini `gemini-3.5-flash-lite` 40/40

## Verdict vs 2026-10-19 cite-optional re-score

| Metric | 2026-10-19 (old adapter e891731c) | 2026-10-20 (soft-strip+honesty a34d2886) |
|--------|-----------------------------------|------------------------------------------|
| useful / label | false / weak_not_useful_yet | false / weak_not_useful_yet |
| correctness mean | 2.525 | **2.65** |
| honesty mean | 2.525 | **2.50** |
| persona_leakage | 5.0 | 5.0 |
| false_refusal | 0.025 | **0.0** |
| quote_in_passage | 0.075 | 0.10 |
| heading_cited | 0.0 | 0.0 |

Need ≥3.5 correctness/honesty. Soft-strip + honesty batch did **not** clear invent-cite / weak doctrine. Persona/refusal side remains fine. `release_gate=false`.

## Next FT knob

Still **`rag_refusal_slice`** for Hub/Ollama (`fine-tuning/sft-improve-refusal-slice-first`). OT chat needs a different lever than soft-strip alone if usefulness is pursued later.
