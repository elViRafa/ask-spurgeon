# Next CPT — S7 Phase A (continue from S6 LoRA)

**Primary GPU path: Vast.ai** ([`VAST_RUNBOOK_CPT_S7.md`](VAST_RUNBOOK_CPT_S7.md)).
Runpod is secondary (account balance currently blocked — see `pretraining/cpt-s7-gpu-blocked-balance`).

Hub production is S7 s5best SHA `06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432`
(`rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2`; overwritten 2026-09-22). Canonical C: Unsloth **2026.8.22 + torch 2.8**
(`pretraining/cpt-eval-stack-pin-s5`, `pretraining/cpt-hub-s7-overwrite`).

Related: `pretraining/cpt-next-cpt-improvements-prep`, [`NEXT_CPT_MORE_TOKENS.md`](NEXT_CPT_MORE_TOKENS.md),
[`scripts/vast_cpt_s7_orchestrate.ps1`](scripts/vast_cpt_s7_orchestrate.ps1),
[`scripts/vast_cpt_s7_remote_continue_b.sh`](scripts/vast_cpt_s7_remote_continue_b.sh),
[`scripts/s7_remote_continue_b.sh`](scripts/s7_remote_continue_b.sh) (Runpod only),
[`scripts/s7_remote_c_eval.sh`](scripts/s7_remote_c_eval.sh).

---

## Goal

Close remaining **§5** (puritan + confession holdout PPL ≥ 15% better than this C’s Ampere base)
without repeating the S6 HF-resume spike, and without a fresh 1e-5 from base.

| Bucket | Isolation C Δ% | Still need for §5 |
|--------|----------------|-------------------|
| spurgeon | **−10.2%** | keep from regressing |
| puritan | −7.2% | **~−8.4% more** |
| confession | −6.0% | **~−9.5% more** |
| general | −1.8% | OK |

---

## Phase A recipe (same `a_output_v3` mix)

| Knob | Value |
|------|--------|
| Init | S6 LoRA `6aab…` only (`CPT_INIT_ADAPTER`) |
| Optimizer | **new Adam** — `PREV_RUN_CHECKPOINT=` (empty string) |
| Profile | `CPT_CONTINUE_PROFILE=s7` |
| Body / emb LR | **2e-6** / **8e-7** |
| Warmup | **0.04** (~83 of 2064 steps) |
| Scheduler | `cosine_with_min_lr` with `min_lr_rate=0.1` (fallback: plain cosine) |
| max_steps | **2064** (~0.5 packed epoch) |
| eval / save | **50** / **50** |
| min_steps | **500** |
| Composite halt | spurgeon + mix + puritan + confession; patience **4**, ε **0.003** |
| Seed bests | S6 **in-train** @ ckpt-2050 (not isolation-C full-holdout CE) |
| Checkpoints | `/workspace/checkpoints_s7` (never auto-resume `checkpoints_sota`) |
| §5 export | `theology_cpt_lora_s5best/` when mean(puritan, confession) improves and spurgeon ≤ seed+0.01 |
| Spike abort | spurgeon ≥ seed+0.12 on **two** consecutive complete cycles |
| Eval buckets | spurgeon, puritan, confession, **general** (monitor-only; not in composite) |
| Stack | Unsloth **2026.8.22** + torch **2.8** + torchvision **0.23**; omit xformers |
| Mix | `kaggle/a_output_v3` SHA `23dd3820baa0b657cb6528e4fdf1b2d4813c3cfa7b7c982805b4a7ff34990973` |

### Seeded composite bests (in-train @ 2050)

| Metric | Seed |
|--------|------|
| eval_spurgeon_loss | 2.4987 |
| eval_mix_loss | 2.0208 |
| eval_puritan_loss | **1.751** |
| eval_confession_loss | **1.668** |

Do **not** replace puritan/confession with isolation-C values (1.722 / 1.662) — those use
full holdouts (20 / 10 docs), not `EVAL_DOCS_PER_BUCKET=16`.

### Earliest composite halt math

With seeds set, first scored cycle is step **500**. Patience 4 + eval_steps 50 → earliest
halt at step **650** (not 525). Without the patience bump, seeded bests + patience 2 would
halt at ~25% of budget.

### Landmine

If `PREV_RUN_CHECKPOINT` is **unset** (not empty) and volume still has `checkpoints_sota`,
S6 auto-resume would pick the highest sota ckpt. S7 launcher **always** sets
`PREV_RUN_CHECKPOINT=` on first launch, and `CPT_CONTINUE_PROFILE=s7` only scans
`checkpoints_s7`. Mid-S7 interrupt: `S7_RESUME=1` resumes highest under `checkpoints_s7` only.

Do **not** point `CPT_INIT_ADAPTER` at a checkpoint dir. Do **not** use S5 SHA `ef4df3a3`.

Optional ablation: `CPT_TRAIN_EMBEDDINGS=0` freezes embeds without editing the train script.

---

## Copy onto the pod (`/workspace`)

```text
kaggle/a_output_v3/theology_dataset/          →  /workspace/theology_dataset/
kaggle/a_output_v3/theology_holdouts/         →  /workspace/theology_holdouts/
data/theology_mix_manifest.json               →  /workspace/theology_mix_manifest.json
# Nested S6 LoRA (6aab), e.g. Hub download or:
# vast_cpt_s6/fetch/theology_cpt_lora/theology_cpt_lora/  →  /workspace/theology_cpt_lora/
scripts/train_cpt_sota.py
scripts/cpt_runtime.py
scripts/s7_remote_continue_b.sh
scripts/s7_remote_c_eval.sh
scripts/eval_cpt_sota.py
```

Do **not** copy S5 `ef4df3a3` adapter. Do **not** rebuild the mix for Phase A.

---

## Launch — Vast (primary)

Dry (no rent):

```powershell
cd continued_pretrain\scripts
.\vast_cpt_s7_orchestrate.ps1
```

Go (after dry credit/offer report):

```powershell
cd continued_pretrain\scripts
.\vast_cpt_s7_orchestrate.ps1 -Go -StartMonitor
```

Uses Miniforge env `unsloth_cpt_s7` + torch **2.8** / Unsloth **2026.8.22** (do **not** run
`s7_remote_continue_b.sh` on Vast — system pip SIGSEGV). Init = nested S6 LoRA `6aab…`
(flattened). Never ships `checkpoints_sota`. Details: [`VAST_RUNBOOK_CPT_S7.md`](VAST_RUNBOOK_CPT_S7.md).

## Launch — Runpod (secondary; currently balance-blocked)

```bash
bash /workspace/s7_remote_continue_b.sh
# Mid-S7 interrupt resume only:
# S7_RESUME=1 bash /workspace/s7_remote_continue_b.sh
```

Monitor (local Runpod): pass total steps so progress is not stuck on S6’s 4128:

```powershell
.\s6_start_monitor.ps1 -TotalSteps 2064
# or: $env:CPT_TOTAL_STEPS=2064
```

Env knobs (optional overrides): `LEARNING_RATE`, `EMBEDDING_LEARNING_RATE`,
`CONTINUE_MAX_STEPS`, `EARLY_STOP_MIN_STEPS`, `COMPOSITE_SEED_BESTS` (JSON),
`CPT_TRAIN_EMBEDDINGS`, `ABORT_SPURGEON_DELTA`.

---

## C eval after B

```bash
# Prefers theology_cpt_lora_s5best; falls back to theology_cpt_lora.
# Pin SHA after B finishes (do not leave eval default at S6 6aab).
EXPECTED_ADAPTER_SHA256=<s7_sha> bash /workspace/s7_remote_c_eval.sh
```

Artifacts: HF best → `theology_cpt_lora/` (spurgeon metric); §5 candidate →
`theology_cpt_lora_s5best/` + `s5_best.json`.

---

## Win / keep / abort

- **Win:** puritan and confession Δ% vs *this* C base ≤ −15%, spurgeon not worse than ~12.85 by
  more than ~1 PPL, general ≤ +10% vs base. C on Unsloth 2026.8.22 / torch 2.8 only.
- **Keep Hub S6:** any C that loses puritan/confession vs 5.60 / 5.27, or spurgeon > 13.3.
- **Abort mid-B (enforced):** spurgeon ≥ seed+0.12 (~2.619) on two consecutive complete cycles
  after min_steps. Manual: train loss jump ≥ 0.3 in 10 steps (S6 resume-spike signature).

---

## Do not

- Create a pod until operator says go
- HF-resume 2050 / 2100 / 2400 from `checkpoints_sota`
- Fresh 1e-5 from base; another 4e-6 S6 clone; WSD schedule
- C on Unsloth 2026.9.x / torch 2.11
- Seed composite with isolation-C full-holdout CE
- Mix rebuild again / Hub overwrite / merge until a winning Phase B C

## Later — holdout-sibling replay (ready 2026-09-23)

Phase B plateaued at step 750/955 (composite ε=0.003 × 4 evals). Isolation C on
nested s5best `ddbbee3a` slightly beat Hub `06354dfc` but missed §5:

| Bucket | Phase B C | Δ% vs Ampere | Hub `06354dfc` |
|--------|-----------|--------------|----------------|
| spurgeon | **12.39** | −13.42% | 12.45 |
| puritan | **5.50** | −8.88% | 5.52 |
| confession | **5.25** | −6.37% | 5.27 |
| general | 11.88 | −1.34% | — |

Do **not** retrain `a_output_v5`. Next CPT: copy **`kaggle/a_output_v6`**, init
Phase B C-winner `ddbbee3a…`, new Adam, body LR **2e-6**. Halt on Spurgeon +
Puritan + confession only (drop `eval_mix_loss`). Same min 400 / patience 4 / ε 0.003.
Stack Unsloth **2026.8.22** + torch **2.8**. Hub stays `06354dfc` until C wins
Puritan and confession without Spurgeon past ~13.3. No GPU until operator go.

### Continue pack `a_output_v6` (2026-09-23)

| Item | Value |
|------|--------|
| Path | `continued_pretrain/kaggle/a_output_v6` |
| Mix txt | `continued_pretrain/data/mix_v6/theology_mix_train.txt` |
| `mix_sha256` | `2d5a99c1a0d4d3e4d64013dabe894a52f4de1bf0b576e8997b02af595f691acd` |
| Train docs | 23,139 (HF train 22,907 / val 232) |
| Verified tokens | ~42.4M (Qwen3.5-4B-Base, sample ratio 0.3005) |
| Sibling share | **25.0%** (5,661 docs / 35.1M chars; train siblings of pinned puritan + confession holdouts) |
| Spurgeon floor | **35.0%** |
| New-author cap | **5.0%** (Downame / wave 5 leftover) |
| Shares | puritan 49.5% / spurgeon 35.0% / confession 9.2% / general 5.4% / bible 0.9% |
| Holdouts | pinned v3 (puritan 20, confession 10, spurgeon 298) |
| Init | nested Phase B s5best `ddbbee3ac9ef7baf6cca21dcdb844d027d39f5f6a4b88ba10fcf8a43fa7c8214` |
| Halt composite | spurgeon + puritan + confession (**no mix-val**) |
| `CONTINUE_MAX_STEPS` | **955** |
| `EARLY_STOP_MIN_STEPS` | **400** |
| Session / results | `vast_cpt_s7_replay` |

Confession 9.2% is holdout-sibling upweight of existing S4 systematics (Institutes,
Dabney, Gill, Shedd, Witsius), not Shaw / Sum of Saving Knowledge. Leave S5 out.

```text
python continued_pretrain/scripts/07_build_theology_mix.py ^
  --target-spurgeon-share 0.45 --keep-all-spurgeon --max-other-weight 1.5 ^
  --max-confession-share 0.06 --replay-frac 0.10 ^
  --replay-txt continued_pretrain/data/replay/general_replay.txt ^
  --puritan-holdout continued_pretrain/data/holdouts_pinned_v3/puritan_holdout.txt ^
  --confession-holdout continued_pretrain/data/holdouts_pinned_v3/confession_holdout.txt ^
  --spurgeon-holdout continued_pretrain/data/holdouts_pinned_v3/spurgeon_holdout.txt ^
  --holdout-sibling-share 0.25 --out-dir continued_pretrain/data/mix_v6

python continued_pretrain/scripts/06_verify_tokens.py --mix --data-dir continued_pretrain/data/mix_v6

py -3.13 continued_pretrain/scripts/18_prep_hf_dataset.py ^
  --train-txt continued_pretrain/data/mix_v6/theology_mix_train.txt ^
  --manifest continued_pretrain/data/mix_v6/theology_mix_manifest.json ^
  --holdout-dir continued_pretrain/data/holdouts_pinned_v3 ^
  --out-dir continued_pretrain/kaggle/a_output_v6 --allow-continue-reweight
```

### Frozen continue pack `a_output_v5` (2026-09-23)

| Item | Value |
|------|--------|
| Path | `continued_pretrain/kaggle/a_output_v5` |
| Mix txt | `continued_pretrain/data/mix_v5/theology_mix_train.txt` |
| `mix_sha256` | `61e830575138935cdf6c1b029a3128e096ff4e3633e44a464b3957b9d6e78285` |
| Train docs | 15,420 (HF train 15,265 / val 155) |
| Verified tokens | ~25.1M (Qwen3.5-4B-Base, sample ratio 0.2701) |
| New-author share | **15.0%** (2,454 docs / 13.9M chars; one pass, no copies) |
| Shares | puritan 54.2% / spurgeon 33.8% / general 6.3% / confession 4.5% / bible 1.2% |
| Holdouts | pinned v3 (puritan 20, confession 10, spurgeon 298) |
| `CONTINUE_MAX_STEPS` | **955** (one packed epoch, batch 16) |
| `EARLY_STOP_MIN_STEPS` | **400** |
| Composite seeds | spurgeon 2.4987 / puritan 1.751 / confession 1.668 — **no `eval_mix_loss` seed** |

### Uniform shelf `a_output_v4` (frozen)

### Mix `a_output_v4` (2026-09-23)

| Item | Value |
|------|--------|
| Path | `continued_pretrain/kaggle/a_output_v4` |
| `mix_sha256` | `37a3ba50aa9efb8057d9d36227ac4547f08d35a31ccd71cf3f2d20f928131c81` |
| Train docs | 54,799 (HF train 54,251 / val 548) |
| Verified tokens | ~94.7M (Qwen3.5-4B-Base, sample ratio 0.2848) |
| Shares | puritan 47.8% / spurgeon 38.4% / general 7.2% / confession 5.3% / bible 1.3% |
| Holdouts | pinned v3 (puritan 20, confession 10) match |

### Shelf on disk (in this mix)

| Key | Path | Source |
|-----|------|--------|
| `downame_christian_warfare` | `data/puritans/downame/christian_warfare.txt` | EEBO-TCP `A20752` (~1.65M chars) |
| `downame_guide_godliness` | `data/puritans/downame/guide_to_godliness.txt` | EEBO-TCP `A20762` (~4.06M chars) |
| `ambrose_looking_unto_jesus` | `data/puritans/ambrose/looking_unto_jesus.txt` | EEBO-TCP `A25241` (~2.82M chars) |
| `swinnock_works` | `data/puritans/swinnock/works_1665.txt` | EEBO-TCP `A62040` (~1.65M chars) |
| `swinnock_incomparableness` | `data/puritans/swinnock/incomparableness_of_god.txt` | EEBO-TCP `A62054` (~0.36M chars) |
| `venning_plague_of_plagues` | `data/puritans/venning/plague_of_plagues.txt` | EEBO-TCP `A64834` (~0.60M chars) |
| `binning_sinners_sanctuary` | `data/puritans/binning/sinners_sanctuary.txt` | EEBO-TCP `A28173` (~0.74M chars) |
| `preston_breastplate` | `data/puritans/preston/breastplate_of_faith_and_love.txt` | EEBO-TCP `A09950` (~0.93M chars) |
| `durham_unsearchable_riches` | `data/puritans/durham/unsearchable_riches_of_christ.txt` | EEBO-TCP `B02840` (~0.69M chars) |
| `vincent_unseen_christ` | `data/puritans/vincent/true_christians_love_of_the_unseen_christ.txt` | EEBO-TCP `A64995` (~0.27M chars) |
| `guthrie_great_interest` | `data/puritans/guthrie/christians_great_interest.txt` | CCEL `guthrie/interest2` (~0.41M chars) |

Wave 5 (2026-09-23) added **~8.47M chars** of new-author practical divinity. Long-s already
normalized in `clean_pd_text`. Train-only: do **not** redraw puritan/confession holdouts.

S5 confession catalog is wired (`--s5`: Shaw + Sum of Saving Knowledge) but **not fetched**.
This mix's confession share is **5.3%** (all 2,763 train docs; no cap fire). Adding Shaw
would still risk evicting existing S4 confession under a later rebuild. Leave S5 out.

### Holdouts

- Live probes: `continued_pretrain/data/holdouts/{puritan,confession}_holdout.txt`
- Snapshot: `continued_pretrain/data/holdouts_pinned_v3/` (SHA backup before v4)
- `07_build_theology_mix.py` now **pins** those files when present (same fingerprint
  rule as Spurgeon). New Downame and wave 5 docs stay in **train**.

### Mix rebuild (v4 uniform 2026-09-23; v5 reweight same day)

v4 uniform pack is frozen. v5 is the isolated continue-reweight (`--out-dir data/mix_v5`,
`--continue-reweight-share 0.15`). Do **not** overwrite either pack. Commands for v5:

```text
python continued_pretrain/scripts/07_build_theology_mix.py ^
  --target-spurgeon-share 0.45 --keep-all-spurgeon --max-other-weight 1.5 ^
  --max-confession-share 0.06 --replay-frac 0.10 ^
  --replay-txt continued_pretrain/data/replay/general_replay.txt ^
  --puritan-holdout continued_pretrain/data/holdouts_pinned_v3/puritan_holdout.txt ^
  --confession-holdout continued_pretrain/data/holdouts_pinned_v3/confession_holdout.txt ^
  --spurgeon-holdout continued_pretrain/data/holdouts_pinned_v3/spurgeon_holdout.txt ^
  --continue-reweight-share 0.15 --out-dir continued_pretrain/data/mix_v5

python continued_pretrain/scripts/06_verify_tokens.py --mix --data-dir continued_pretrain/data/mix_v5

py -3.13 continued_pretrain/scripts/18_prep_hf_dataset.py ^
  --train-txt continued_pretrain/data/mix_v5/theology_mix_train.txt ^
  --manifest continued_pretrain/data/mix_v5/theology_mix_manifest.json ^
  --holdout-dir continued_pretrain/data/holdouts_pinned_v3 ^
  --out-dir continued_pretrain/kaggle/a_output_v5 --allow-continue-reweight
```

### Phase C (unchanged)

- Merge winner → new r=64 LoRA
