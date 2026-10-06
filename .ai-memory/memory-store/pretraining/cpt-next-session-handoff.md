---
store_path: pretraining/cpt-next-session-handoff
title: "CPT next-session handoff"
summary: "Cursor analysis first; Isolation C for resume SHA 22698039 pending; no GPU until Rafael go"
priority: high
tags: [cpt, s8, handoff, isolation-c, cursor, m_hi]
schema_version: 1.3
last_updated: "2026-10-06T17:13:00-03:00"
evidence: [pretraining/cpt-current, pretraining/cpt-s8-mhi-resume-complete, episodic/2026-10-06]
---

# CPT next-session handoff

## For Cursor analysis (entry point)

Rafael asked Foundry to **stop** Isolation C shipping / GPU handoff and wait for **Cursor analysis**.

### Candidate for Isolation C (not rented)

| Field | Value |
|-------|--------|
| Adapter SHA | `2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207` |
| Paths (same SHA) | `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s8_mhi_resume/fetch/mhi_resume/theology_cpt_lora` and `.../checkpoints/checkpoint-2250` |
| In-train | puritan **1.701** / Spurgeon **2.449** |
| Proxy note | ≤1.670 not met; operator still wanted C before pause |
| Stack | Unsloth 2026.8.22 + torch 2.8 (`vast_remote_stack_isolation_c.sh`, not S6 torch 2.11) |
| Base pattern | merge `a70fded8` / eval vs stock Qwen3.5-4B-Base as prior C |
| Pack / holdouts | `a_output_v6_p0` |
| §5 win | puritan loss ≤ **1.6349** (−15% vs ref); Spurgeon not worse → then Hub; else keep Phase A `06354dfc` |

### Foundry was about to ship (stopped mid-task)

- `NEXT_CPT_S8_MHI_RESUME_C.md`
- dryable `vast_cpt_s8_mhi_resume_c_eval.ps1` + readiness (clone S7 C pattern, default dry, `-Go` rents)
- Results dir would be `vast_cpt_s8_mhi_resume_c`

Do **not** run S6/S7 C scripts as-is for this adapter.

### Also useful context

- Continue cleared in-train break: 1.708/2.456 @800 (`vast_cpt_s8_mhi_continue/fetch`)
- max_seq_length→max_length remap: PR #7 merged (`99c7a42`); cosine fallback no longer mis-fires
- s8 continue profile restore: PR #8 may still be open / local
- Playbooks on disk: `NEXT_CPT_S8_MHI_CONTINUE.md`, `NEXT_CPT_S8_MHI_RESUME.md`, `NEXT_CPT_S8_SWEEP.md`

### Do not

- Rent GPU / Forge -Go for C until Rafael says so after Cursor
- Hub-push
- HF-resume `checkpoints_sota`
