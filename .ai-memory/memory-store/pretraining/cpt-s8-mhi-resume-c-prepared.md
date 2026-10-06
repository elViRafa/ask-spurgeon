---
store_path: pretraining/cpt-s8-mhi-resume-c-prepared
title: "S8 m_hi resume Isolation C prepared"
summary: "Cursor prepared Isolation C for the m_hi resume best adapter"
priority: high
tags: [cpt, s8, m_hi, isolation-c, forge]
schema_version: 1.3
last_updated: "2026-10-06T20:53:55+00:00"
evidence: [continued_pretrain/scripts/vast_cpt_s8_mhi_resume_c_eval.ps1, "commit:e104c25"]
---

Cursor prepared Isolation C for the m_hi resume best adapter. No GPU was rented and Hub was not pushed.

| Field | Value |
|-------|--------|
| PR | draft https://github.com/elViRafa/ask-spurgeon/pull/9 branch `cursor/s8-mhi-resume-isolation-c-468d` commit `e104c25` |
| SHA | `2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207` |
| AdapterDir | flat theology_cpt_lora under vast_cpt_s8_mhi_resume/fetch/mhi_resume |
| Same SHA | checkpoint-2250 is a cross-check only |
| In-train | puritan 1.701 / Spurgeon 2.449 |
| Proxy | ≤1.670 missed by +0.031 nats |
| §5 | puritan loss ≤ 1.6349 (minus 15 percent PPL). Spurgeon not worse than stock base in the same C |
| Expected C | miss. Probe is about minus 9.2 percent PPL. Gap to the gate is +0.066 nats. Continue plus resume only moved 1.723 to 1.701 |
| Pack | a_output_v6_p0 |
| Stack | Unsloth 2026.8.22 + torch 2.8 via vast_remote_stack_isolation_c.sh |
| Fetch | vast_cpt_s8_mhi_resume_c |
| Hub | stay Phase A 06354dfc until section 5 wins |

Playbook: NEXT_CPT_S8_MHI_RESUME_C.md in continued_pretrain.
Dry script: vast_cpt_s8_mhi_resume_c_eval.ps1 (readiness only, no vastai).
-Go rents one GPU. Pytest test_vast_cpt_s8_mhi_resume_c_eval.py passed (6). Readiness fails closed until the operator PC has the flat adapter and v6_p0 holdouts.

## Grok Bot

Call Forge for Isolation C. Foundry does not rent. Forge may run the dry script on the operator PC from branch cursor/s8-mhi-resume-isolation-c-468d, or from main after PR 9 merges. Forge may pass -Go only after Rafael says go. Do not train again. Do not Hub-push. A paid C is a confirmation expected to miss section 5.
