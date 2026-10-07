---
store_path: fine-tuning/qa-teacher-quote-fidelity-prompt
title: "QA teacher prompt — quote fidelity fix"
summary: "`fine_tuning/scripts/rewrite_qa_answers_teacher.py` TEACHER_SYSTEM rule 5 strengthened:"
priority: high
tags: [sft, qa-mix, rewrite, prompt]
schema_version: 1.3
last_updated: "2026-08-29T17:17:58-04:00"
review_status: stale
---

# QA teacher quote-fidelity prompt fix (2026-08-29)

## Change
`fine_tuning/scripts/rewrite_qa_answers_teacher.py` TEACHER_SYSTEM rule 5 strengthened:
- Quotes must be verbatim copy-paste contiguous CONTEXT substrings (character-for-character: punctuation, hyphens, commas)
- Explicit BAD/GOOD examples added (paraphrase "most thorough", truncated "the profit that he makes by it,", exact "battle-field of sin.")
- Validation in `qa_rewrite_checks.py` unchanged (`norm_ws(q) in ctx_n`)

## Smoke after fix
- **Gemini 2.5 Flash**: 0/3 ok (lines 225–227) — still paraphrases/truncates
- **Cerebras gpt-oss-120b**: 2/3 ok (lines 225–227) — meets ≥2/3 bar

## Batch (Cerebras, limit 50)
- 22 ok / 28 dropped (~44% pass); frequent 429 rate limits
- Merged 24 **new** unique answers (103 total bulk ok in pending; 103 merged cumulative)

## Post-merge audit
- quote **261/2657 (9.8%)** — still GATE <10% but rising from 9.1%
- teacherish **123** (gold 20 + bulk 103)
- caricature **0**
- 13_sft_local_readiness **PASS**

## Recommendation
- Use **Cerebras** for bulk batches; avoid Gemini for quote-heavy rewrites until prompt or model improves
- Continue ~50-row batches; target quote ≥10–15% before GPU
- Optional: `--rerun-ok` on near-miss dropped rows with Cerebras
