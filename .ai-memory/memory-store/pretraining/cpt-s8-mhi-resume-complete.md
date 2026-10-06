---
store_path: pretraining/cpt-s8-mhi-resume-complete
title: "S8 m_hi resume complete (ckpt-2250)"
summary: "HF-resume from continue checkpoint-800 with optimizer (MAX_STEPS 2400, LR 5e-6 constant)"
priority: low
tags: [cpt, s8, m_hi, resume, fetch]
schema_version: 1.3
last_updated: "2026-10-06T20:53:55+00:00"
evidence: [continued_pretrain/scripts/vast_cpt_s8_mhi_resume_c_eval.ps1, "commit:e104c25"]
---

HF-resume from continue checkpoint-800 with optimizer (MAX_STEPS 2400, LR 5e-6 constant).

- Best adapter SHA: `2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207`
- Location: vast_cpt_s8_mhi_resume/fetch/mhi_resume/theology_cpt_lora (= checkpoint-2250)
- In-train: puritan 1.701 / Spurgeon 2.449
- Proxy ≤1.670 not met
- Isolation C playbook is prepared in draft PR 9. See pretraining/cpt-s8-mhi-resume-c-prepared. Forge may dry; -Go waits for Rafael
- Hub: still Phase A 06354dfc
