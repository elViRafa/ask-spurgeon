# Next CPT — S8 m_hi resume Isolation C

Prepared from the Grok Bot CPT memories (sweep, continue, resume). **Not rented.**
Hub stays Phase A `06354dfc` until this C wins §5. Cursor / Foundry do not pass `-Go`.

Stack: Unsloth **2026.8.22** + torch **2.8** via `vast_remote_stack_isolation_c.sh`.
Do not use `vast_remote_c_eval.sh` (S6 torch 2.11).

## Candidate

| Field | Value |
|-------|--------|
| Adapter SHA256 | `2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207` |
| AdapterDir (flat) | `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s8_mhi_resume/fetch/mhi_resume/theology_cpt_lora` |
| Same SHA | `.../fetch/mhi_resume/checkpoints/checkpoint-2250` (also accept `.../fetch/checkpoints/checkpoint-2250` as a cross-check only) |
| In-train | puritan **1.701** / Spurgeon **2.449** |
| Pack / holdouts | `kaggle/a_output_v6_p0` (mix SHA `ad817213`) |
| Train base | merge parent P0 `a70fded8` → `/workspace/theology_cpt_merged_a70`, then this fresh LoRA |
| C comparison | stock `unsloth/Qwen3.5-4B-Base`, same protocol as prior Isolation C (`EVAL_BASE` in `eval_cpt_sota.py`) |
| Fetch dir | `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s8_mhi_resume_c` |
| Session file | `.../vast_cpt_s8_mhi_resume_c_session.json` |

Prefer the flat `theology_cpt_lora` leaf as AdapterDir. Do not point AdapterDir at `checkpoint-2250`, and do not point it at any S6 or S7 fetch tree.

## In-train path (already finished)

| Stage | Puritan | Spurgeon | Note |
|-------|---------|----------|------|
| S8 sweep m_hi | 1.723 | 2.469 | break ≤1.7204 **MISS** |
| m_hi continue @800 | 1.708 | 2.456 | break **CLEARED** |
| m_hi resume ckpt-2250 | **1.701** | **2.449** | proxy ≤**1.670** **not met** |
| Proxy | ≤1.670 | | about −12.0% PPL vs the §5 reference |
| §5 | ≤**1.6349** | not worse than stock base on this C | −15% puritan PPL |

Resume was HF-resume from continue checkpoint-800 (MAX_STEPS 2400, LR 5e-6 constant). Best weights are checkpoint-2250, copied to the flat leaf above. Both copies must hash to `22698039…`.

## Is C still justified?

Prepare the scripts. Do not treat a future `-Go` as a likely Hub promote.

§5 puritan loss ≤ **1.6349** is −15% perplexity versus the stock-base reference implied by that ceiling: `exp(1.6349) / 0.85 ≈ 6.034` PPL (gate PPL ≈ 5.129). The resume probe is `exp(1.701) ≈ 5.479` PPL, about **−9.2%**, the same band as P0 Isolation C (puritan about −9.45%), which failed §5. The proxy 1.670 is `exp(1.670) ≈ 5.312` PPL (**−12.0%**). The miss versus the proxy is **+0.031** nats; the miss versus §5 is **+0.066** nats.

Continue plus resume only moved puritan **1.723 → 1.701** (0.022). A favorable full-holdout versus 16-doc gap of ~0.03, the order seen on older C runs, would land near **1.672**, still about **0.037** above 1.6349. In-train numbers are `EVAL_DOCS_PER_BUCKET=16`. Isolation C scores the full pinned holdouts (puritan 20, confession 10, Spurgeon 298). Those are different measurements. Spurgeon 2.449 is `exp(2.449) ≈ 11.58` PPL on the 16-doc probe, not the 298-doc holdout.

So this C is a confirmation eval that should be expected to **miss** §5. It is still the only score that can promote or kill the adapter. Until it wins, Hub stays Phase A `06354dfc`.

## §5 (after fetch)

Win only if the fetched `theology_cpt_eval_metrics.json` shows both:

- puritan loss ≤ **1.6349** (−15% PPL vs the stock base scored in this same run)
- Spurgeon not worse than that stock base (`delta_vs_base_pct.spurgeon` ≤ 0)

Otherwise keep Phase A `06354dfc`. Do not Hub-push a near miss. Do not merge.

## Dry (no vastai, no rent)

Operator PC, after the flat adapter and `a_output_v6_p0` holdouts are on disk:

```powershell
cd continued_pretrain\scripts
.\vast_cpt_s8_mhi_resume_c_eval.ps1
```

Equivalent readiness-only check:

```powershell
python continued_pretrain\scripts\vast_cpt_s8_mhi_resume_c_eval_readiness.py
```

Dry runs readiness and exits 0. It does not load the Vast helpers, search offers, or create an instance. `READY` requires the flat file SHA `22698039…`, a matching checkpoint-2250 cross-check, `a_output_v6_p0` holdout buckets, and the dry-by-default wiring. A Phase A `06354dfc` file is a hard fail.

## `-Go` (Forge, only after Rafael says go)

```powershell
cd continued_pretrain\scripts
.\vast_cpt_s8_mhi_resume_c_eval.ps1 -Go
```

What `-Go` does: rent **one** GPU (4090, else 3090), sync the flat adapter + `a_output_v6_p0` holdouts, run `vast_remote_stack_isolation_c.sh`, fetch into `vast_cpt_s8_mhi_resume_c`, destroy on success. Pass `-KeepInstance` to keep the instance after a successful fetch. A failed eval keeps the instance for log inspection (same as S7 C); destroy it with `fine_tuning\scripts\vast_destroy.ps1` when finished. Optional: `-Go -OfferId <id>`.

Credit check on `-Go` is about `$2`. Memory after the continue close was about `$3.86`. Re-check live credit before renting. Wall cap is 4 hours, disk 80 GB.

If `from_pretrained` fails because `adapter_config.json` names the pod-local merge `/workspace/theology_cpt_merged_a70`, stop. Do not rewrite the adapter onto stock Qwen and do not score Phase A instead. The LoRA was trained on merged `a70fded8`; the report baseline is still stock `unsloth/Qwen3.5-4B-Base`.

## Do not

- Run `-Go`, `vastai`, or any S8 train orchestrate `-Go` from Cursor, Foundry, or this prep PR
- Hub-push or overwrite `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` (Phase A `06354dfc`)
- Score S6 `6aab`, S5 `ef4df3a3`, S7 Phase A `06354dfc`, Phase B `ddbbee3a`, replay `0289f1c9`, or merge-parent `a70fded8` as this candidate
- Point AdapterDir at `checkpoint-2250` or at `vast_cpt_s6` / `vast_cpt_s7_*`
- Launch `vast_remote_c_eval.sh` or install torch 2.11 / floating Unsloth
- HF-resume `checkpoints_sota` / 2050 / 2400
- Overwrite `a_output_v3` / `v4` / `v5` / `v6` or the Phase A fetch tree
- Re-run the S8 sweep, m_hi continue, or m_hi resume as a new GPU session
