# Next CPT — S8 m_hi resume (dry-ready, not rented)

The S8 sweep missed the in-train break. The m_hi continue then **broke it**
(puritan **1.7082** at step 800, line was **1.7204**). Isolation C was not
run. Estimated C is still short of section 5 (about **1.673** vs **1.6349**,
roughly −11.6% PPL vs −15%).

The leftover plateau is not “the optimizer cannot move.” It is wasted steps:

- Steps 1–400 of the continue replayed the same pack / seed 42 batches.
  Puritan only returned to **1.7229** at step 400.
- New Adam + warmup 0 bumped 1.7226 → 1.7462 by step 100.
- Real progress was steps 400–800: **1.7229 → 1.7082**, still falling
  about **0.0014 / 50 steps**.

This job is one knob: **HF-resume checkpoint-800 with optimizer, RNG, and
sampler position**. Same 5e-6 constant floor. 1600 new steps
(`MAX_STEPS=2400`). No new Adam. No batch replay.

Hub stays Phase A `06354dfc`. No merge and no train happen from the dry command.

## Dry (no rent)

```powershell
cd continued_pretrain\scripts
.\vast_cpt_s8_mhi_resume_orchestrate.ps1
```

Expect `READY` and `DRY COMPLETE`. That command does not call vastai, scp, or ssh.

## Go (one RTX 4090, about 6–8 h train)

Forge runs this only after Rafael says go, on `C:\Users\rafael\Projetos\search-sermons`:

```powershell
cd continued_pretrain\scripts
.\vast_cpt_s8_mhi_resume_orchestrate.ps1 -Go
```

Re-check Vast credit is at least $5 and instance count is 0. Last noted
balance after the continue fetch was about $5.87. Do not pass `-AllowLowCredit`.

The pod merges P0 adapter `a70fded8` into `/workspace/theology_cpt_merged_a70`,
copies the continue adapter out of `/workspace/ckpt800` into
`/workspace/mhi_lora`, then HF-resumes `/workspace/ckpt800`
(SHA `8c1db3db74bcf03b876740a5cf8884899fb3efda4945a2ae74a02655a8359b84`).

| Knob | Value |
|------|--------|
| Mode | `continue`, profile `s8` |
| Init | `/workspace/mhi_lora` (adapter only) |
| Resume | `/workspace/ckpt800` (optimizer + rng + scheduler) |
| Base | fresh merge of `a70fded8` |
| Body LR | **5e-6** |
| Embedding LR | **5e-7** |
| Warmup | 0 |
| Scheduler | constant |
| Steps | 2400 (800 already done + 1600 new), early-stop floor 2400 |
| Rank | 128 / alpha 64 from the loaded adapter |

Stack pin: Unsloth 2026.8.22 + torch 2.8. The merge checks `a70fded8`.
The train process checks `8c1db3db`. Pack `a_output_v6_p0` SHA `ad817213`.

## Decision

In-train break (≤ **1.7204**) already passed. This run is for isolation C.

- Proxy: best in-train puritan ≤ **1.670** (about 0.035 above the C line),
  Spurgeon ≤ **2.490**, general within base +2%.
- Then run isolation C on the same pod before destroy
  (`eval_cpt_sota.py`, stock Qwen3.5-4B-Base, pinned holdout bytes).
- Promote to Hub only if C shows puritan −15% (loss ≤ **1.6349**) and
  Spurgeon is not worse. Otherwise keep Phase A.

At the last continue slope, 1600 new steps are about 0.045 nats. That is
enough to reach the proxy if the curve does not flatten.

## Walk away

`/workspace/mhi_resume/cpt_train.log` must show `cpt_run_mode=continue`,
base `/workspace/theology_cpt_merged_a70`, `init_adapter=/workspace/mhi_lora`,
`PREV_RUN_CHECKPOINT=/workspace/ckpt800`, `r=128`, `lr=5e-6`, and
`max_steps=2400`. The launcher must print `RECIPE_OK` before training
starts. If that block differs, `PREV_RUN_CHECKPOINT` is empty, or the log
says `falling back to cosine`, stop the process. Do not edit scripts on
the instance.

The Unsloth TRL-patch warning is a status note. The continue finished with
it. It is not a reason to patch the pod.

## Fetch

There is no fetch script. Before destroy, copy
`/workspace/mhi_resume_launcher.log` and `/workspace/mhi_resume` into
`continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s8_mhi_resume/fetch`,
including checkpoint optimizer files. Do not skip them.
Done marker: `VAST_CPT_S8_MHI_RESUME_DONE`.

## Do not

- Run `vast_cpt_s8_mhi_continue_orchestrate.ps1`. That continue already ran
  and starts new Adam from the S8 sweep adapter.
- Run `vast_cpt_s8_sweep_orchestrate.ps1`.
- Leave `PREV_RUN_CHECKPOINT` empty. That is the waste this job exists to stop.
- Restart body LR at 5e-5.
- Change the mix, seed, or rank in the same run.
- Run P1 or S7 as its own GPU session.
- HF-resume `checkpoints_sota`.
- Hub-push.
