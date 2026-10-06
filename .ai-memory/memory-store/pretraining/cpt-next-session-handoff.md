---
store_path: pretraining/cpt-next-session-handoff
title: "CPT next-session handoff"
summary: "Isolation C scripts are in draft PR 9"
priority: high
tags: [cpt, s8, handoff, isolation-c, forge]
schema_version: 1.3
last_updated: "2026-10-06T20:53:55+00:00"
evidence: [continued_pretrain/scripts/vast_cpt_s8_mhi_resume_c_eval.ps1, "commit:e104c25"]
---

Isolation C scripts are in draft PR 9. GPU rent stays blocked until Rafael says go.

### Candidate

| Field | Value |
|-------|--------|
| Adapter SHA | `2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207` |
| AdapterDir | flat theology_cpt_lora under vast_cpt_s8_mhi_resume/fetch/mhi_resume |
| Same SHA | checkpoint-2250 (cross-check only) |
| In-train | puritan 1.701 / Spurgeon 2.449 (proxy ≤1.670 missed) |
| §5 | puritan loss ≤ 1.6349; Spurgeon not worse than stock base. Expected result is a miss (about minus 9.2 percent PPL versus minus 15 percent) |
| Stack | Unsloth 2026.8.22 + torch 2.8 (vast_remote_stack_isolation_c.sh) |
| Pack | a_output_v6_p0 |
| Hub | Phase A 06354dfc |
| PR | https://github.com/elViRafa/ask-spurgeon/pull/9 |

### Forge commands (operator PC)

Dry, no rent:

```powershell
cd continued_pretrain\scripts
.\vast_cpt_s8_mhi_resume_c_eval.ps1
```

-Go only after Rafael says go:

```powershell
.\vast_cpt_s8_mhi_resume_c_eval.ps1 -Go
```

Call Forge for this eval. Checkout cursor/s8-mhi-resume-isolation-c-468d until PR 9 merges.

### Do not

- Rent or Hub-push before Rafael says go
- Ask Foundry to run -Go
- Point C at S6 or S7 adapters, or at checkpoint-2250 as AdapterDir
- Use vast_remote_c_eval.sh or torch 2.11
- HF-resume checkpoints_sota
