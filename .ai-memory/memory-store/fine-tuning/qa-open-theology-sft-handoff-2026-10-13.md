# Open-theology QA SFT handoff (2026-10-13)

- Export: fine_tuning/data/qa_open_theology/sft/ at main 30f3682 (local, unpushed). Train 558 rows, eval 40/40.
- Excluded 4 rows (sft/excluded_ids.json): confession-003, confession-023, puritan-087 (junk passages), spurgeon-083 (openrouter/free).
- 150 'the passage' rows regenerated via requeue --requeue-accepted (34c5960); prompt rules 4a (quote format) and 6a (no passage wording).
- 300 more jobs appended (900 total); Clerk hourly groq retry until 2026-10-20, re-exports + commits on completion.
- Cursor: read sft/README.md. Separate dataset with own weight, assistant-only loss, never merge into qa_mix_train / RAG mix. Real GPU run on the final export.
- GPU: Vast credit ~5.41 USD; top-up + operator go to Ask Spurgeon GPU before any rent. No Hub upload.
