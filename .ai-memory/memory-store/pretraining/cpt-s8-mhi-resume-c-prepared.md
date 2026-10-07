---
store_path: pretraining/cpt-s8-mhi-resume-c-prepared
title: "S8 m_hi resume Isolation C prepared"
summary: "Operator will run Isolation C in Grok Bot from PR 10"
priority: high
tags: [cpt, s8, isolation-c, grok, forge]
schema_version: 1.3
last_updated: "2026-10-07T07:58:18-03:00"
evidence: [continued_pretrain/scripts/vast_cpt_s8_mhi_resume_c_eval.ps1, "commit:638a249"]
---

Operator will run Isolation C in Grok Bot from PR 10. Cursor does not rent.

| Field | Value |
|-------|--------|
| PR | https://github.com/elViRafa/ask-spurgeon/pull/10 branch `fix/s8-mhi-resume-c-merge-parent` commit `638a249` |
| SHA | `2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207` |
| AdapterDir | flat theology_cpt_lora under vast_cpt_s8_mhi_resume/fetch/mhi_resume |
| Merge parent | a70fded8 rebuilt to /workspace/theology_cpt_merged_a70 before from_pretrained. Do not remap onto stock Qwen |
| Dry | READY on operator PC 2026-10-07 |
| Vast snapshot | $6.34, 0 instances at 07:56 America/Sao_Paulo. Re-check before -Go |
| §5 | puritan loss ≤ 1.6349. Expected miss |
| Hub | Phase A 06354dfc |

Forge command is in grok/s8-mhi-resume-c-run. main lacks the merge rebuild.
