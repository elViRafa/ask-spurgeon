---
store_path: fine-tuning/sft-track-a-batch1-complete
title: "SFT Track A batch 1 complete"
summary: "- Teacher dry-run + Groq apply 50 rows; merge 24; zip + readiness PASS"
priority: medium
tags: [sft, bulk-rewrite, batch1]
schema_version: 1.3
last_updated: "2026-08-29T09:43:48-04:00"
---

# SFT Track A batch 1 complete (ready state)

**When:** 2026-08-29

## Done this arc
- Teacher dry-run + Groq apply 50 rows; merge 24; zip + readiness PASS
- Fixed teacher defaults to `openai/gpt-oss-120b`; Windows UTF-8 print fix
- Decision recorded: SFT QA Spurgeon-only (no multi-writer assistant mix)

## Ready for next session
- Continue bulk: `--provider groq --limit 50` (resume from bulk_pending 50 lines)
- Or GPU dry-run only if operator says go (no CPT volume)

## Counts snapshot
train 2923; gold 20; bulk merged 24; pending attempts 50 (24 ok / 26 drop ~48%)
