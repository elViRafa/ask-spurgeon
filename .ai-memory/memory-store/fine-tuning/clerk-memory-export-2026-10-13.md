# Clerk memory export (open-theology QA), 2026-10-13

## Role and rules
- Clerk administers the open-theology QA slice in fine_tuning/data/qa_open_theology/ (spec: fine_tuning/GROK_BOT_CLERK.md).
- Q&A is authored only by the teacher via generate_open_theology_qa.py; keys stay in .env.
- --apply runs need Rafael's go. Halt at reject rate >40% or 3 consecutive teacher/check failures (fix prompt/catalog, never silent retry).
- Never: build_qa_mix_v2.py, edit qa_mix_train.jsonl or qa_test_frozen.jsonl, merge this slice into qa_mix or the RAG mix, GPU rent, Hub upload.

## Teacher / providers
- Groq openai/gpt-oss-120b is the working teacher; daily limit 200k tokens (~70-100 rows/day). A 429 leaves the job pending (not a reject); rerun with --clear-halt.
- OpenRouter key hit spend limit (403); Gemini 2.5-flash quota exhausted after 18 rows; Cerebras returns 402.

## History
- Oct 9-11: first 600 train jobs; checker, heading, max_tokens (1500) and 429 fixes by Foundry (PR #13, merged ba0f9af).
- Oct 12: train 569/31 of 600; eval 40/40 accepted.
- Oct 13: 151 rows with "the passage/text/excerpt" wording requeued (--requeue-accepted) and regenerated: train 562 accepted / 38 rejected, eval 40/40.
- SFT export (export_open_theology_sft.py --apply): train 558 / eval 40 at commit 30f3682. Excluded: confession-003, confession-023, puritan-087, spurgeon-083.
- 300 new train jobs appended (900 total), generating on Groq hourly; final export + local commit when done.

## For Cursor
- Use fine_tuning/data/qa_open_theology/sft/ (read sft/README.md and README_HANDOFF.md). Load as its own dataset, train on assistant turn only, never merge into qa_mix_train.
- Re-run the export before the real GPU run to pick up the final 900-job rows.
