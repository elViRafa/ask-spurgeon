---
store_path: fine-tuning/post-sft-eval-results
title: "Post-SFT evaluation results"
summary: "Compared local Ollama `spurgeon-qa-v2` against `spurgeon-cpt` on all 100 frozen fixed-context examples, using deterministic raw ChatML generation and 200 order-swapped judgments from a pinned independ"
priority: medium
tags: [sft, evaluation, ollama, cpt, release-gate]
schema_version: 1.3
last_updated: "2026-09-07T22:16:54-04:00"
evidence: [fine_tuning/eval_results/post_sft_eval.json, fine_tuning/eval_results/post_sft_eval_human_review.md, fine_tuning/scripts/evaluate.py]
---

# Post-SFT evaluation complete (2026-09-07)

Compared local Ollama `spurgeon-qa-v2` against `spurgeon-cpt` on all 100 frozen fixed-context examples, using deterministic raw ChatML generation and 200 order-swapped judgments from a pinned independent judge.

## Results
- Candidate groundedness: **4.51/5** vs CPT **2.485/5**.
- Candidate judge wins: **171/200**.
- Refusal recall: **54%** (27/50), below required **85%**.
- Corruption: **0%**; context echo: **0%**; leaked turns: **0%**; stop compliance: **100%**.
- Verdict: **release gates FAIL solely on refusal recall**. Do not change app defaults or treat the model as release-ready.

## Evidence
- Full report: `fine_tuning/eval_results/post_sft_eval.json`
- Human review: `fine_tuning/eval_results/post_sft_eval_human_review.md`
- Focused tests: 16 passed.
- Full pytest collection is blocked by unrelated vendored llama.cpp dependency imports.
