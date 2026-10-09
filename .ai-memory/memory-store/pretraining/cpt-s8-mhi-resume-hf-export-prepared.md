---
store_path: pretraining/cpt-s8-mhi-resume-hf-export-prepared
title: "S8 m_hi resume merged HF export prepared"
summary: "Experimental upload path"
priority: high
tags: [cpt, s8, merge, hf-export, merged-16bit]
schema_version: 1.3
last_updated: "2026-10-07T09:43:18-03:00"
evidence: [continued_pretrain/NEXT_CPT_S8_MHI_RESUME_HF_EXPORT.md, fine_tuning/scripts/merge_cpt_s8_mhi_resume.py]
---

# S8 m_hi resume merged 16-bit HF export (prepared 2026-10-07)

Experimental upload path. **Do not** overwrite production CPT LoRA v2 (`rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2`, Phase A `06354dfc`). Isolation C §5 miss stands.

## Artifacts

| Step | Path / repo |
|------|-------------|
| Runbook | `[REDACTED_SECRET].md` |
| Two-stage merge | `fine_tuning/scripts/merge_cpt_s8_mhi_resume.py` |
| Readiness | `fine_tuning/scripts/cpt_s8_mhi_resume_merge_readiness.py` |
| Pod merge | `fine_tuning/scripts/cpt_remote_merge_s8_mhi_resume.sh` |
| Hub upload | `fine_tuning/scripts/upload_cpt_s8_mhi_resume_merged_hf.py` |
| Tests | `fine_tuning/scripts/test_merge_cpt_s8_mhi_resume_readiness.py` |

## Merge chain

1. P0 s5best LoRA `a70fded8` @ `vast_cpt_s7_p0/fetch/theology_cpt_lora_s5best` → `fine_tuning/models/theology_cpt_merged_a70`
2. Resume LoRA `22698039` @ `vast_cpt_s8_mhi_resume/fetch/mhi_resume/theology_cpt_lora` (patch `adapter_config` base to step 1) → `fine_tuning/models/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit`

Uses existing `merge_cpt_lora.py` twice. Ampere bf16 GPU required; `--cpu` fallback for OOM.

## Default Hub target

`rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit` (private). README marks experimental + §5 miss + general +3.8% vs base.

## Operator commands

```powershell
python fine_tuning\scripts\cpt_s8_mhi_resume_merge_readiness.py
python fine_tuning\scripts\merge_cpt_s8_mhi_resume.py --preflight
python fine_tuning\scripts\merge_cpt_s8_mhi_resume.py
python fine_tuning\scripts\upload_cpt_s8_mhi_resume_merged_hf.py
```

Local readiness printed READY; pytest 2 passed. Merge not run on operator PC (needs GPU).

## Do not

- Overwrite Hub LoRA v2
- Merge resume LoRA on stock Qwen without merged a70 first
- Promote to production or start SFT without explicit decision (general regression)
