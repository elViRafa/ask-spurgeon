---
store_path: pretraining/cpt-current
title: "CPT current status"
summary: "m_hi resume adapter 22698039 is the Isolation C candidate"
priority: high
tags: [cpt, s8, m_hi, resume, isolation-c, status, hub]
schema_version: 1.3
last_updated: "2026-10-06T20:53:55+00:00"
evidence: [continued_pretrain/scripts/vast_cpt_s8_mhi_resume_c_eval.ps1, "commit:e104c25"]
---

m_hi resume adapter 22698039 is the Isolation C candidate. Scripts are in PR 9. Section 5 is still open and a miss is the expected C result.

## Status (canonical)

| Item | Value |
|------|--------|
| Hub production | Phase A s5best 06354dfc — no Hub until Isolation C wins section 5 |
| Best local adapter | m_hi resume LoRA SHA 2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207 at vast_cpt_s8_mhi_resume/fetch/mhi_resume/theology_cpt_lora (= checkpoint-2250) |
| In-train (resume) | puritan 1.701 / Spurgeon 2.449 (proxy ≤1.670 not met, +0.031) |
| Prior continue | m_hi continue at 800: puritan 1.708 / Spurgeon 2.456 — in-train break ≤1.7204 cleared (instance 54372117) |
| S8 sweep | Plateau miss; best m_hi 1.723/2.469 before continue |
| Pack | a_output_v6_p0 / mix SHA ad817213 |
| Merge parent | P0 a70fded8 merged to /workspace/theology_cpt_merged_a70 |
| section-5 / Isolation C | Puritan loss ≤ 1.6349 (minus 15 percent). Scripts ready in PR 9. Expected C miss (about minus 9.2 percent PPL). Forge may dry; -Go only after Rafael says go |
| Vast | 0 instances expected; credit was about $3.86 after continue close |
| Stack pin | Unsloth 2026.8.22 + torch 2.8 |

## Timeline

1. S8 sweep (54312477): miss, fetch vast_cpt_s8_sweep
2. m_hi continue (54372117): gate cleared 1.708/2.456, fetch vast_cpt_s8_mhi_continue
3. m_hi resume (HF-resume ckpt-800 to 2400): best ckpt-2250 SHA 22698039, fetch vast_cpt_s8_mhi_resume
4. Isolation C playbook and dry-by-default scripts: PR 9. No rent yet

## Do not

- Forge -Go or any rent for Isolation C until Rafael says go
- Hub-push or overwrite Phase A
- Ask Foundry to rent
- Re-run the S8 sweep, S7, or P1 as a new GPU session
