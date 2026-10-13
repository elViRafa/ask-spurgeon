# Foundry memory export (2026-10-13) - for Cursor

## Standing rules
- Always allowed: read metrics, propose one-knob recipe changes, open PRs. Needs Rafael's explicit go: GPU rent, Hub overwrite, GGUF upload, rebuilding qa_mix_v2, tokenizer id changes.
- One knob per PR; proof = tests or a dry orchestrator. Never log tokens; never speak as Spurgeon; never HF-resume sota checkpoints.
- GPU work goes to Ask Spurgeon GPU (Forge). Vast credit ~5.41 USD; needs a top-up + go.
- The open-theology QA slice (fine_tuning/data/qa_open_theology/) is SFT data but stays a SEPARATE side set: never merge it into qa_mix_train.jsonl or the RAG mix.
- For complex items Rafael wants Cursor analysis first, before any GPU.

## CPT history
- S8 sweep (2026-10-05, Vast 54312477): pack a_output_v6_p0 SHA ad817213; merge P0 a70fded8, then three r=128 alpha=64 arms @400 steps, metric_for_best=eval_puritan_loss. Best puritan/Spurgeon: m_lo 1.725/2.470, m_hi 1.723/2.469, f_hi 1.736/2.488. Break needed puritan <=1.7204 and Spurgeon <=2.490 -> plateau MISS.
- m_hi continue (2026-10-05): gate cleared (puritan 1.708 / Spurgeon 2.456); artifacts under vast_cpt_s8_mhi_continue/fetch.
- m_hi resume best adapter SHA 2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207 (vast_cpt_s8_mhi_resume/fetch/mhi_resume/theology_cpt_lora, checkpoint-2250); in-train puritan 1.701 / Spurgeon 2.449. Stack Unsloth 2026.8.22 + torch 2.8.
- Isolation C (2026-10-07, instance 54630561): puritan 1.660 vs Sec.5 gate <=1.6349 -> MISS; Spurgeon 2.475 (stock 2.661, puritan stock 1.797). Results under vast_cpt_s8_mhi_resume_c/.
  - Earlier fails: rc=4, the adapter_config base pointed at a missing /workspace/theology_cpt_merged_a70 (fix: rebuild the a70 merge on the pod, PR #10); rc=2, CRLF in vast_remote_stack_isolation_c.sh (fix 0988137, .gitattributes *.sh eol=lf).
- HF export (2026-10-07): local 16-bit merged model at fine_tuning/models/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit (LOCAL_MERGED_OK). Not on the Hub. parents[2] IndexError fix landed in PR #11.
- Hub stays Phase A 06354dfc until a candidate wins Sec.5.

## Open-theology QA
- See qa-open-theology-sft-handoff-2026-10-13.md, sft/README.md and README_HANDOFF.md.
- Teacher: groq gpt-oss-120b (free tier ~200k tokens/day); a few rows from gemini-2.5-flash. A 429 is a quota stop, not a reject.
- Prompt rules: bracketed catalog heading; 4a quote format (double quotes, no OCR fixes, no title as quote); 6a no 'the passage' wording.
