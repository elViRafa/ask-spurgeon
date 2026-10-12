# Next CPT — S8 m_hi continue (dry-ready, not rented)

S8 sweep finished. Best arm `m_hi` puritan **1.7226**, **0.0022** short of **1.7204**, still falling at step 400. Spurgeon **2.4694**. This job continues that LoRA for 800 steps at the learning rate the cosine had already reached. It does not rerun the three-arm sweep.

Hub stays Phase A `06354dfc`. No merge and no train happen from the dry command.

## Dry (no rent)

```powershell
cd continued_pretrain\scripts
.\vast_cpt_s8_mhi_continue_orchestrate.ps1
```

Expect `READY` and `DRY COMPLETE`. That command does not call vastai, scp, or ssh.

## Go (one RTX 4090, about 3–4 h)

Forge runs this only after Rafael says go, on `C:\Users\rafael\Projetos\search-sermons`:

```powershell
cd continued_pretrain\scripts
.\vast_cpt_s8_mhi_continue_orchestrate.ps1 -Go
```

Re-check Vast credit is at least $5 and instance count is 0. Last noted balance after the S8 destroy was about $5.87. Do not pass `-AllowLowCredit`.

The pod merges P0 adapter `a70fded8` into `/workspace/theology_cpt_merged_a70`, then continues the fetched `m_hi` LoRA (`15781d964f6ca053033b08ddf9154634493513d20c9b4699faa7936fc0fe2754`) on pack `a_output_v6_p0` (SHA `ad817213`).

| Knob | Value |
|------|--------|
| Mode | `continue`, profile `s8`, empty `PREV_RUN_CHECKPOINT` (new Adam) |
| Init | `/workspace/m_hi_lora` |
| Base | fresh merge of `a70fded8` |
| Body LR | **5e-6** (cosine floor of the 5e-5 / 400-step run) |
| Embedding LR | **5e-7** |
| Warmup | 0 |
| Scheduler | constant |
| Steps | 800, early-stop floor 800 |
| Rank | 128 / alpha 64 from the loaded adapter |

Stack pin: Unsloth 2026.8.22 + torch 2.8. The merge checks `a70fded8`. The train process checks `15781d96`. Do not leave the a70 pin in `EXPECTED_ADAPTER_SHA256` for training.

## Decision

Plateau is broken if best in-train puritan loss is at least **0.015** below **1.7354** (≤ **1.7204**), Spurgeon stays at or under **2.490**, and general stays within base +2%. Then run isolation C. Promote to Hub only if C shows puritan −15% and Spurgeon is not worse. Otherwise keep Phase A.

## Walk away

`/workspace/mhi_continue/cpt_train.log` must show `cpt_run_mode=continue`, base `/workspace/theology_cpt_merged_a70`, `init_adapter=/workspace/m_hi_lora`, `r=128`, `lr=5e-6`, and `max_steps=800`. The launcher must print `RECIPE_OK` before training starts. If that block differs, or the log says `falling back to cosine`, stop the process. Do not edit scripts on the instance.

The Unsloth line about the TRL trainer patch is a status note. S8 finished with that warning. It is not a reason to patch the pod.

## Fetch

There is no fetch script. Before destroy, copy `/workspace/mhi_continue_launcher.log` and `/workspace/mhi_continue` into `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s8_mhi_continue/fetch`, including checkpoint optimizer files. Do not skip them. Done marker: `VAST_CPT_S8_MHI_CONTINUE_DONE`.

## Do not

- Run `vast_cpt_s8_sweep_orchestrate.ps1`. That sweep is finished and starts three fresh LoRAs.
- Edit `train_cpt_sota.py`, the plan, or the remote on the instance.
- Run P1 or S7 as its own GPU session.
- Change the mix in the same run.
- Restart body LR at 5e-5. That rewarms the cosine about 10× above the floor this curve finished on.
- HF-resume `checkpoints_sota`.
- Hub-push.
