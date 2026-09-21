---
store_path: pretraining/cpt-current
title: "CPT current — S6 LoRA good on S5 stack; Hub overwrite pending approve"
summary: "**Stack isolation:** `pretraining/cpt-s6-stack-isolation-c`"
priority: medium
tags: [cpt, s6, hub-v2, stack-isolation]
schema_version: 1.3
last_updated: "2026-09-20T18:17:21-03:00"
summary_hash: ae50844218c68cf398ceb1a89e8e955d
evidence: [pretraining/cpt-s6-c-eval-regression-diagnosis, pretraining/cpt-s6-c-eval-complete]
---

# CPT — current pointer (2026-09-20)

**Stack isolation:** `pretraining/cpt-s6-stack-isolation-c`  
**Prior Vast C (false FAIL):** `pretraining/cpt-s6-c-eval-regression-diagnosis`

| Item | Status |
|------|--------|
| S6 B (Vast) | DONE — best ckpt-2050 SHA `6aab9194…` |
| S6 C Vast torch 2.11 | DONE ×2 — **false FAIL** (+27.9%) |
| Stack-isolation C (Unsloth 2026.8.22 / torch 2.8) | DONE — spurgeon **12.85 (−10.2%)** |
| Hub production | still `…-theology-cpt-lora-v2` until **separate** overwrite approve |
| New B | not needed to “fix C”; optional only for §5 −15% |
| SFT | still on Hub-v2-merged path until Hub decision |
