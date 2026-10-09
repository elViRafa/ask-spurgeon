# Next CPT — S8 sweep (finished 2026-10-05, plateau MISS)

Do not launch this sweep again. Best arm was `m_hi` at puritan 1.7226. The continue then reached 1.7082. The next job is [`NEXT_CPT_S8_MHI_RESUME.md`](NEXT_CPT_S8_MHI_RESUME.md).

The 2e-6 / r=32 continues barely moved puritan loss (~0.004 nats per run). Mix and metric knobs cannot show until the optimizer can move the weights. This sweep was that test. It ran and missed the in-train break (puritan ≤ 1.7204).

Hub stays Phase A `06354dfc`. No merge and no train happen from this checklist's dry command.

## Dry (no rent)

```powershell
cd continued_pretrain\scripts
.\vast_cpt_s8_sweep_orchestrate.ps1
```

Expect `READY` and `DRY COMPLETE`. That command does not call vastai, scp, or ssh.

## Go (already ran — do not rent this again)

```powershell
cd continued_pretrain\scripts
.\vast_cpt_s8_sweep_orchestrate.ps1 -Go
```

The pod merges P0 adapter `a70fded8` into `/workspace/theology_cpt_merged_a70`, then runs three fresh LoRAs on pack `a_output_v6_p0` (SHA `ad817213`). Each arm is 400 steps, r=128, alpha=64, warmup 0.05, cosine floor 10% of peak, abort-at-50 off, early-stop floor at step 400. New Adam. Optimizer state stays in checkpoints.

| Arm | Base | Body LR | Embedding LR |
|-----|------|---------|--------------|
| m_lo | merged `a70fded8` | 2e-5 | 2e-6 |
| m_hi | merged `a70fded8` | 5e-5 | 5e-6 |
| f_hi | `unsloth/Qwen3.5-4B-Base` | 5e-5 | 5e-6 |

Stack pin: Unsloth 2026.8.22 + torch 2.8. If r=128 OOMs, that arm retries once at r=64, alpha=45 (same rsLoRA scale).

A loss bump in the first 50–100 steps of a merged arm is expected. Do not abort on it.

## Decision

Plateau is broken if an arm's best in-train puritan loss is at least **0.015** below **1.7354** (the replay checkpoint-600 band), Spurgeon stays at or under **2.490**, and general stays within base +2%. Then run isolation C on that checkpoint (per-document losses, bootstrap CI, and the clean sub-score). The pinned holdout bytes stay the gate.

Promote to Hub only if C shows puritan −15% and Spurgeon is not worse. Otherwise keep Phase A.

## Do not

- Run P1 (`metric_for_best` only) as its own GPU session. The sweep already selects on puritan loss.
- Change the mix in the same run.
- Edit pinned holdout bytes.
- HF-resume `checkpoints_sota`.
