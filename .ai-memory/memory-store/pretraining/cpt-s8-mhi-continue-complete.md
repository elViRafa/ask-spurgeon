---
store_path: pretraining/cpt-s8-mhi-continue-complete
title: "S8 m_hi continue ran: in-train puritan 1.7082, C not run"
summary: "Forge rented and ran the m_hi continue the same afternoon (ARM_START ~16:20, VAST_CPT_S8_MHI_CONTINUE_DONE, fetch ~19:44 America/Sao_Paulo)"
priority: low
tags: [cpt, s8, m_hi, continue, results, plateau]
schema_version: 1.3
last_updated: "2026-10-05T21:17:42-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s8_mhi_continue/fetch/mhi_continue/checkpoints/checkpoint-800/trainer_state.json, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s8_mhi_continue/fetch/mhi_continue_launcher.log]
---

# S8 m_hi continue complete (2026-10-05, Forge)

Forge rented and ran the m_hi continue the same afternoon (ARM_START ~16:20, VAST_CPT_S8_MHI_CONTINUE_DONE, fetch ~19:44 America/Sao_Paulo). Nothing was recorded in memory at the time.

- Recipe as planned: merged a70fded8 base, init m_hi 15781d96, r=128 alpha=64, body 5e-6 / emb 5e-7, constant, warmup 0, 800 steps, new Adam. RECIPE_OK printed.
- Output adapter SHA `8c1db3db74bcf03b876740a5cf8884899fb3efda4945a2ae74a02655a8359b84` (checkpoint-800 = theology_cpt_lora). optimizer.pt fetched (1.7 GB).
- In-train puritan: 50:1.7404, 100:1.7462, 200:1.7403, 400:1.7229, 450:1.7195, 600:1.7138, 800:**1.7082** (best, still falling ~0.0015/50).
- Spurgeon 2.4560, confession 1.6262, general 2.5079, mix 2.0546 at step 800.
- In-train break line (<=1.7204) passed from step 450. Isolation C NOT run yet. Hub stays Phase A 06354dfc.

## Waste found
- Steps 1-400 replayed the exact batches m_hi had just trained on (same pack, SEED 42, same sampler order). Train loss there was 1.60 vs 1.90 first time.
- New Adam + warmup 0 bumped puritan 1.7226 -> 1.7462 by step 100; it only got back to 1.7229 at step 400. All real progress was steps 400-800.
- Pod log: "fast path is not available ... Falling back to torch implementation" (flash-linear-attention missing). ~2,250 tok/s on a 4090.

Estimated isolation C (in-train vs C offset ~0.035 from replay): puritan ~1.673 loss, ~-11.6% PPL. Section 5 needs <= 1.6349 (-15%).
