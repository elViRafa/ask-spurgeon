---
store_path: pretraining/cpt-s8-sweep-ready
title: "S8 sweep go is given to Forge"
summary: "Operator go is given (2026-10-05)"
priority: high
tags: [cpt, s8, go, forge]
schema_version: 1.3
last_updated: "2026-10-05T09:06:17-03:00"
evidence: [continued_pretrain/NEXT_CPT_S8_SWEEP.md, continued_pretrain/scripts/vast_cpt_s8_sweep_orchestrate.ps1, continued_pretrain/scripts/vast_cpt_s8_sweep_remote.sh]
---

Operator go is given (2026-10-05). Forge runs `continued_pretrain/scripts/vast_cpt_s8_sweep_orchestrate.ps1 -Go` on `C:\Users\rafael\Projetos\search-sermons`. Dry already printed READY earlier the same morning. Live credit was about $7.98 with zero instances at 09:03 America/Sao_Paulo. Re-check credit >= $5 before rent.

Pod merges `a70fded8` via `merge_cpt_lora.py` into `/workspace/theology_cpt_merged_a70`, then three fresh r=128 alpha=64 arms on `a_output_v6_p0` SHA `ad817213`: m_lo LR 2e-5, m_hi LR 5e-5, f_hi stock base LR 5e-5. 400 steps each. Abort-at-50 off. OOM retries r=64 alpha=45. Stack Unsloth 2026.8.22 + torch 2.8.

Break rule: best in-train puritan loss <= 1.7204, Spurgeon <= 2.490, general within base +2%. Then isolation C. Hub stays Phase A `06354dfc`. Do not run P1. Do not change the mix.
