---
store_path: fine-tuning/qa-mix-size-vs-refusal
title: "QA mix size is enough; refusal slice is the later knob"
summary: "Do not grow the whole QA mix before the S8 SFT run"
priority: high
tags: [sft, qa-mix, refusal, decision]
schema_version: 1.3
last_updated: "2026-10-09T10:17:18-03:00"
evidence: [fine_tuning/data/qa_mix_manifest.json, fine_tuning/eval_results/post_sft_eval.json]
---

Do not grow the whole QA mix before the S8 SFT run. Train is already 3264 rows (answerable 2793, refusal 370 at 11.34%, multiturn 100, catechism overlay 241). The frozen test is 50 answerable / 50 refusal. GATE-0 confusion was tp 27, fp 1, tn 49, fn 23: refusal recall 0.54, precision 0.96, false-refusal rate 0.02. Format, stop, and judge groundedness already passed.

More copies of the same sermon answers would dilute the 11% refusal share. The useful later knob, after the S8 base run, is a harder refusal slice under the same system prompt (near-miss context, anachronism, CPT knowledge the chunks do not support). Keep speakers Spurgeon-sermon-heavy. Do not add a second system prompt. Quote grounding was 0.415 (31/100 ungrounded-quote rows); that is a gold-quality knob, separate from row count.
