---
store_path: pretraining/cpt-next-session-handoff
title: "CPT next-session handoff"
summary: "Rafael will run Isolation C in Grok Bot on 2026-10-07"
priority: high
tags: [cpt, s8, handoff, isolation-c, grok, forge]
schema_version: 1.3
last_updated: "2026-10-07T07:58:11-03:00"
evidence: [continued_pretrain/scripts/vast_cpt_s8_mhi_resume_c_eval.ps1, [REDACTED_SECRET].md, "commit:638a249"]
---

Rafael will run Isolation C in Grok Bot on 2026-10-07. Forge rents. Cursor does not.

Checkout `fix/s8-mhi-resume-c-merge-parent` (`638a249`, PR 10). main does not rebuild `/workspace/theology_cpt_merged_a70`, and that missing path is the rc=4 OSError.

### Candidate

| Field | Value |
|-------|--------|
| Adapter SHA | `2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207` |
| AdapterDir | flat `theology_cpt_lora` under `vast_cpt_s8_mhi_resume/fetch/mhi_resume` |
| Same SHA | checkpoint-2250 (cross-check only) |
| Merge parent | `a70fded8` at `vast_cpt_s7_p0/fetch/theology_cpt_lora_s5best` plus `fine_tuning/scripts/merge_cpt_lora.py` |
| Pod base | rebuild `/workspace/theology_cpt_merged_a70` before `from_pretrained`. Do not remap onto stock Qwen |
| Eval baseline | stock `unsloth/Qwen3.5-4B-Base` |
| In-train | puritan 1.701 / Spurgeon 2.449 |
| §5 | puritan loss ≤ 1.6349; Spurgeon not worse than stock base. Expected miss |
| Stack | Unsloth 2026.8.22 + torch 2.8 |
| Pack | a_output_v6_p0 |
| Hub | Phase A `06354dfc` |
| Dry | READY on the operator PC 2026-10-07 |
| Vast snapshot | $6.34 credit, 0 instances at 07:56 America/Sao_Paulo. Re-check before -Go |

### Forge command

```powershell
```

### Do not

- Launch from main
- Hub-push
- Point AdapterDir at checkpoint-2250 or at an S6/S7 tree
- Train again
