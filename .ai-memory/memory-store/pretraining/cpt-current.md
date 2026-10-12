---
store_path: pretraining/cpt-current
title: "CPT current status"
summary: "Isolation C for m_hi resume adapter 22698039 finished on 2026-10-07"
priority: high
tags: [cpt, s8, hub, merge]
schema_version: 1.3
last_updated: "2026-10-07T11:53:11-03:00"
evidence: [continued_pretrain/scripts/vast_cpt_s8_mhi_resume_c_eval.ps1, "[REDACTED_SECRET].md", "commit:638a249"]
---

Isolation C for m_hi resume adapter 22698039 finished on 2026-10-07. Section 5 miss. Hub stays Phase A 06354dfc.

| Item | Value |
|------|--------|
| Result | Puritan loss 1.6605 vs gate 1.6349. Spurgeon PPL 11.88 (−17.0% vs base). Confession 5.01 (−10.7%). General 12.50 (+3.8% vs base) |
| Fetch | `vast_cpt_s8_mhi_resume_c/theology_cpt_eval_metrics.json` at 08:37 America/Sao_Paulo, rc=0 |
| Hub | Phase A `06354dfc` — do not overwrite |
| Full card | `pretraining/cpt-s8-mhi-resume-isolation-c-complete` |

Do not Hub-push. Do not start another train without operator go.

Merged 16-bit HF export is prepared (not run). See `pretraining/cpt-s8-mhi-resume-hf-export-prepared` and `[REDACTED_SECRET].md`. Default new Hub repo `qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit`; do not overwrite LoRA v2 `06354dfc`.

## Merged 16-bit HF uploaded 2026-10-07

Experimental private Hub: `rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit`. Local `LOCAL_MERGED_OK` then upload. Production LoRA v2 `06354dfc` unchanged. Still not a §5 win.
