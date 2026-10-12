---
store_path: pretraining/cpt-s8-next-is-sft
title: "After S8 Isolation C, next job is SFT"
summary: "After S8 Isolation C (2026-10-07), the next GPU job is SFT on the merged S8 weights, not another CPT resume"
priority: high
tags: [cpt, s8, sft, decision]
schema_version: 1.3
last_updated: "2026-10-09T09:08:40-03:00"
evidence: [fine_tuning/NEXT_SFT_S8.md, fine_tuning/scripts/sft_s8_plan.py, fine_tuning/scripts/vast_sft_s8_orchestrate.ps1]
---

After S8 Isolation C (2026-10-07), the next GPU job is SFT on the merged S8 weights, not another CPT resume.

| Evidence | Value |
|----------|--------|
| Adapter | `22698039` step 2250 |
| Puritan loss | 1.6605 vs gate 1.6349 (gap 0.0256) |
| Last resume slope | in-train puritan 1.708 to 1.701 from step 800 to 2250 |
| General | +3.8% vs untrained base |
| Prior SFT `spurgeon-qa-v2` | groundedness 4.51, refusal 0.54 vs 0.85 |

One knob: base is private Hub `rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit`. QA mix and PEFT 4090 recipe stay. Hub LoRA v2 `06354dfc` stays. `SFT_EXPORT=0` until F gates. If refusal is still the only miss, the next knob is the refusal slice. If groundedness falls under 4.0, keep the adapter experimental.

Dry: `fine_tuning/scripts/vast_sft_s8_orchestrate.ps1` (refuses `-Go`). Pytest `test_sft_s8_plan.py` 5 passed. Runbook `fine_tuning/NEXT_SFT_S8.md`. Forge rents only after a later operator go.
