---
store_path: pretraining/cpt-s8-mhi-resume-hf-export-orchestrator
title: "S8 merge export orchestrator ready for Grok Bot"
summary: "Cursor prepared the S8 m_hi resume 16-bit merge so Grok Bot can rent"
priority: high
tags: [cpt, s8, merge, hf-export, grok, vast]
schema_version: 1.3
last_updated: "2026-10-07T10:05:20-03:00"
evidence: [continued_pretrain/scripts/vast_cpt_s8_mhi_resume_hf_export_orchestrate.ps1, continued_pretrain/NEXT_CPT_S8_MHI_RESUME_HF_EXPORT.md, fine_tuning/scripts/cpt_remote_merge_s8_mhi_resume.sh]
---

Cursor prepared the S8 m_hi resume 16-bit merge so Grok Bot can rent. Cursor does not rent, SSH, fetch, destroy, or upload.

- Orchestrator: `continued_pretrain/scripts/vast_cpt_s8_mhi_resume_hf_export_orchestrate.ps1`
- Dry on 2026-10-07 printed READY. Adapter `22698039`, merge parent `a70fded8`. Fetch disk free about 34.6 GB (gate is 30 GB). No vastai call.
- Pod merge script pins torch 2.8 + Unsloth 2026.8.22 and passes adapter paths to preflight. It does not upload.
- Grok Bot command after operator go: `.\vast_cpt_s8_mhi_resume_hf_export_orchestrate.ps1 -Go` from `continued_pretrain/scripts`.
- Local check before that go: `LOCAL_MERGED_NOT_READY` (folder not fetched yet).
- Hub target after a later local upload: `rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit`. Do not overwrite LoRA v2 `06354dfc`.
- Runbook: `[REDACTED_SECRET].md`
