# CPT S7 v6 holdout-sibling replay — analysis (2026-09-26)

Post-mortem of the continued-pretrain (CPT) run that continued from Phase B nested LoRA `ddbbee3a…` on mix pack `a_output_v6`, then ran isolation C on the early-stop winner. Written for the next recipe decision; numbers come from in-train logs and `vast_cpt_s7_replay_c/theology_cpt_eval_metrics.json`.

## 1. What we ran

| Knob | Value |
|------|--------|
| Session | `vast_cpt_s7_replay` |
| Mix | `a_output_v6` (SHA pin `e050787e…` after new_authors rebuild) |
| Init adapter | nested Phase B LoRA `ddbbee3a…` (new Adam, LR 2e-6) |
| Halt composite | spurgeon + puritan + confession only (not mix-val, not `new_authors`) |
| Stack | Unsloth 2026.8.22 + torch 2.8 |
| Train host | Vast `52805980` (RTX 4090) |
| C host | Vast `52830244` (RTX 4090, Germany) |

**Hub was never updated.** Production Hub stays Phase A s5best `06354dfc…`.

Mid-run crash: TRL 0.24 rejected `max_seq_length` on `SFTConfig`; remapped to `max_length` (PR #2), hot-applied, train recovered.

## 2. Training outcome (Phase B continue)

| Item | Result |
|------|--------|
| Planned steps | 955 |
| Early stop | **600 / 955** (min early-stop 400) |
| Best checkpoint | **checkpoint-550** |
| Exported s5best SHA | `0289f1c9af70615ef4dca58b3e2d7dabc3eefef96c8bdf92bff0933689adeb55` |
| Train loss (late) | ~1.94 |

### In-train CE vs Phase B composite seeds

Seeds used to start this continue (Phase B plateau):

| Bucket | Seed CE | @300 | Late (~500+) |
|--------|---------|------|----------------|
| spurgeon (§5) | 2.499 | 2.482 | ~2.480–2.481 |
| puritan (§5) | 1.751 | 1.738 | ~1.736 |
| confession (§5) | 1.668 | 1.663 | ~1.662 |

In-train CE stayed a hair **under** the seed the whole way. That is useful for early-stop, but it is **not** the ship gate. Ship gate is isolation-C PPL on the holdouts.

Init LoRA on disk remains at `fetch/theology_cpt_lora/` (`ddbbee3a…`). Do **not** confuse that with s5best.

## 3. Isolation C (ship scorecard)

Eval script: `vast_cpt_s7_c_eval.ps1` pinned to flat
`vast_cpt_s7_replay/fetch/theology_cpt_lora_s5best` + holdouts `a_output_v6/theology_holdouts`.
Metrics: `vast_cpt_s7_replay_c/theology_cpt_eval_metrics.json`.

### PPL vs base (and vs prior C)

| Bucket | Base PPL | Replay C | Δ% vs base | Phase B C | Hub Phase A |
|--------|----------|----------|------------|-----------|-------------|
| spurgeon | 14.31 | **12.35** | **−13.69%** | 12.39 (−13.4%) | 12.45 (−13.0%) |
| puritan | 6.03 | **5.48** | **−9.22%** | 5.50 (−8.9%) | 5.52 (−8.6%) |
| confession | 5.61 | **5.22** | **−6.88%** | 5.25 (−6.4%) | 5.27 (−6.0%) |
| general (monitor) | 12.04 | 11.83 | −1.78% | ~11.88 | ~11.95 |
| new_authors (monitor) | 11.65 | 9.96 | −14.53% | — | — |

Train probe spurgeon (16 docs): PPL **11.79** (−11.36% vs base 13.30).

### §5 gate

Need ≤ **−15%** on spurgeon + puritan + confession (all three).

| Bucket | Δ% | Need | Pass? |
|--------|-----|------|-------|
| spurgeon | −13.69 | −15 | no |
| puritan | −9.22 | −15 | no |
| confession | −6.88 | −15 | no |

**Verdict: §5 FAIL.** Hair better than Phase B C on every §5 bucket, still short of the bar. Closest bucket is spurgeon (~1.3 pp short of −15%). Puritan and confession remain the bottleneck (~6 and ~8 pp short).

### Auxiliary signals

From the same metrics JSON:

| Signal | Result |
|--------|--------|
| MCQ WSC | base 0.70 → v2 **0.76** |
| MCQ Heidelberg | base 0.43 → v2 **0.45** |
| Greedy style probes | high repetition on 2/3 prompts (ratios ~0.61–0.63) |
| Greedy doctrine | one severe loop (ratio ~0.77 on “faith rests upon Christ alone”) |
| Forgetting probes | still answer basic world facts (Paris / photosynthesis / Industrial Revolution) |

Repetition warnings mean the adapter improved holdout PPL a little without fixing (and maybe slightly worsening) loopiness on open generation. Next recipe should not ignore that.

## 4. Interpretation

1. **Holdout-sibling replay moved the needle in the right direction, but tiny.** Same stack, continue from `ddbbee3a`, v6 mix: ~0.04 / 0.02 / 0.03 PPL better than Phase B C. Not a Hub promotion.
2. **Early-stop behaved.** Best at 550, halt at 600 — composite did not keep improving enough to justify full 955.
3. **Spurgeon is nearest to §5; puritan/confession are not.** Further “more of the same” continue is unlikely to close a 6–8 pp confession gap alone.
4. **`new_authors` monitor dropped a lot (−14.5%)** while general barely moved (−1.8%). That is a probe, not a gate. It suggests the v6 pack / new-authors exposure is landing somewhere, but not converting into confession/puritan §5.
5. **Generation quality risk.** Isolation C PPL can improve while greedy completions loop. Any next win needs to watch repetition, not only PPL.

## 5. Artifacts to keep

| Artifact | Path |
|----------|------|
| Continue-from pin | `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_replay/CONTINUE_FROM.json` |
| Best adapter | `.../vast_cpt_s7_replay/fetch/theology_cpt_lora_s5best/` (SHA `0289f1c9…`) |
| Same weights | `.../checkpoints_s7/checkpoint-550/` |
| C metrics | `.../vast_cpt_s7_replay_c/theology_cpt_eval_metrics.json` |
| Memory notes | `.ai-memory/memory-store/pretraining/cpt-s7-replay-isolation-c-complete.md` |

**Next CPT init (when there is a go):** this adapter + **new Adam**. Do not Hub-overwrite until §5 clears.

## 6. Candidate next knobs (one at a time)

Do not combine. Pick with evidence:

1. **Confession/puritan reweight or curated mix slice** — largest §5 deficit is confession, then puritan.
2. **Longer / lower-LR continue from `0289f1c9`** — only if early-stop curve suggests under-training; this run already plateaued by 550–600.
3. **Regularization against loops** (decode/eval first, train knob only if probes stay bad after a mix change).
4. **Do not** redraw holdouts, raise LR casually, HF-resume sota checkpoints, or Hub-push on this C.

## 7. Ops notes

- Destroy-after-C is standing policy (no idle GPU after metrics fetch).
- Both Vast instances for this cycle were destroyed; credit left ~$5.8 after C.
- PR #3 on `main` (`052a890`) pinned C eval + continue-from memories.

## 8. One-line summary

v6 replay from `ddbbee3a` early-stopped at checkpoint-550 (`0289f1c9…`); isolation C is the best local §5 so far (12.35 / 5.48 / 5.22) but still FAIL vs −15%; Hub stays Phase A; continue from this adapter only after a new operator go and a **single** next knob aimed at confession/puritan (and watch repetition).

## P0 follow-up (2026-09-28)

Built `mix_v6_p0` / `a_output_v6_p0` with `--target-confession-share 0.15` (Spurgeon pinned 35%, puritan 50%). Dry orchestrator green. Next GPU: init `0289f1c9`, new Adam, session `vast_cpt_s7_p0` — needs go.
