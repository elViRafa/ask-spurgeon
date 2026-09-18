---
store_path: fine-tuning/post-sft-eval-2026-09-07
title: "Post-SFT frozen evaluation complete"
summary: "Full post-SFT evaluation completed on all 100 frozen fixed-context examples (50 answerable, 50 refusal), comparing Ollama `spurgeon-qa-v2` against `spurgeon-cpt` with identical raw ChatML and temperat"
priority: medium
tags: [sft, evaluation, ollama, gemini, gates]
schema_version: 1.3
last_updated: "2026-09-07T22:16:20-04:00"
evidence: [fine_tuning/eval_results/post_sft_eval.json, fine_tuning/eval_results/post_sft_eval_human_review.md, fine_tuning/data/qa_test_frozen.sha256]
---

Full post-SFT evaluation completed on all 100 frozen fixed-context examples (50 answerable, 50 refusal), comparing Ollama `spurgeon-qa-v2` against `spurgeon-cpt` with identical raw ChatML and temperature 0. Gemini 3.5 Flash Lite judged 200 order-swapped pairs: candidate groundedness 4.51, correctness 4.455, citation quality 4.19, honesty 4.49, style 4.615; candidate won 171/200 judgments vs 21 losses and 8 ties. Deterministic SFT results: format 100%, echo 0%, corruption 0%, valid citations 100%, stop 100%, leaked turns 0%, false-refusal 2%, but refusal recall only 54% (27/50), precision 96.43%, F1 69.23%, and 2% persona violations. Release verdict: FAIL only the refusal-recall >=85% hard gate; export remains blocked. Baseline was much worse: groundedness 2.485, corruption 24%, echo 9%, refusal recall 18%, stop 78%.
