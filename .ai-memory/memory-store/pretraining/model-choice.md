---
store_path: pretraining/model-choice
title: "Pretraining Step 4 — Model Choice & Technical Rationale"
summary: "Pretraining Step 4 — Model Choice & Technical Rationale"
priority: medium
tags: [pretraining, model, qwen, vram]
schema_version: 1.3
last_updated: "2026-06-06T19:33:37-04:00"
---

Technical rationale for choosing unsloth/Qwen2.5-3B (base model) for continued pretraining on Spurgeon's sermons. The model's 151,643 BPE vocabulary natively represents 19th-century English registers (thee, thou, hast) without excessive subword fragmentation. Detailed VRAM budgeting allocates ~7.55 GB out of 16 GB on a single T4 GPU, leaving massive headroom for packed training. Rationale covers choosing not to train input embeddings or lm_head to save VRAM and maintain gradient stability, while setting lora_dropout=0 enables Unsloth's fused Triton kernels.
