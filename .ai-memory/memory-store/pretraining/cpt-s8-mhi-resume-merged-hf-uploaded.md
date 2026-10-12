---
store_path: pretraining/cpt-s8-mhi-resume-merged-hf-uploaded
title: "S8 m_hi resume merged 16-bit on Hub"
summary: "Uploaded experimental S8 m_hi resume merged 16-bit HF on 2026-10-07 after LOCAL_MERGED_OK"
priority: high
tags: [cpt, s8, merge, hf-export, hub]
schema_version: 1.3
last_updated: "2026-10-07T11:53:09-03:00"
evidence: [fine_tuning/scripts/upload_cpt_s8_mhi_resume_merged_hf.py, fine_tuning/models/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit]
---

Uploaded experimental S8 m_hi resume merged 16-bit HF on 2026-10-07 after LOCAL_MERGED_OK.

| Field | Value |
|-------|--------|
| Hub | https://huggingface.co/rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit (private) |
| Local | `fine_tuning/models/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit` |
| Shards | 8.46 GiB (2 safetensors) + config + tokenizer |
| Resume LoRA | `22698039` |
| Merge parent | `a70fded8` |
| Isolation C | §5 miss; general +3.8% vs base |

Production LoRA v2 `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` (`06354dfc`) unchanged. Not a §5 promote. Do not start SFT on this base without an explicit decision.
