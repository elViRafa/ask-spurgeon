---
store_path: grok/s8-mhi-resume-c-run
title: "Grok Bot runs S8 m_hi resume Isolation C"
summary: "Rafael will run this Isolation C in Grok Bot (Forge), not in Cursor"
priority: high
tags: [grok, forge, cpt, s8, isolation-c]
schema_version: 1.3
last_updated: "2026-10-07T07:58:15-03:00"
evidence: [continued_pretrain/scripts/vast_cpt_s8_mhi_resume_c_eval.ps1, [REDACTED_SECRET].md, "commit:638a249"]
---

Rafael will run this Isolation C in Grok Bot (Forge), not in Cursor.

Use branch `fix/s8-mhi-resume-c-merge-parent` commit `638a249` (open PR 10). Dry on the operator PC printed READY on 2026-10-07. Live Vast at 07:56 America/Sao_Paulo was credit $6.34 and 0 instances. Re-check credit and instances, then:

```powershell
cd C:\Users\rafael\Projetos\search-sermons
git checkout fix/s8-mhi-resume-c-merge-parent
cd continued_pretrain\scripts
.\vast_cpt_s8_mhi_resume_c_eval.ps1 -Go
```

`-Go` syncs resume adapter `2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207` plus merge parent `a70fded8` and `merge_cpt_lora.py`, rebuilds `/workspace/theology_cpt_merged_a70`, then evals on Unsloth 2026.8.22 + torch 2.8. Do not remap the adapter onto stock Qwen. EVAL_BASE stays `unsloth/Qwen3.5-4B-Base`.

Section 5 win only if puritan loss ≤ 1.6349 and Spurgeon is not worse than the stock base in that same run. A miss is expected. Hub stays Phase A `06354dfc`. Fetch into `vast_cpt_s8_mhi_resume_c`. Destroy the instance only after a successful fetch. Do not train. Do not launch from main.
