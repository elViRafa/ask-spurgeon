---
store_path: pretraining/cpt-b-eval-strategy
title: "CPT B eval strategy — verified next-B spec"
summary: "Operator approved this as the continue-session spec (nits from fact-check applied)"
priority: high
tags: [cpt, eval, early-stop, handoff, corpus-v3]
schema_version: 1.3
last_updated: "2026-08-28T00:14:06-04:00"
evidence: [continued_pretrain/scripts/train_cpt_sota.py, continued_pretrain/scripts/18_prep_hf_dataset.py, continued_pretrain/kaggle/runpod_cpt_v3/cpt_train.log, continued_pretrain/kaggle/runpod_cpt_v3/theology_cpt_eval_metrics.json, continued_pretrain/NEXT_CPT_MORE_TOKENS.md, continued_pretrain/kaggle/c_output/C_EVAL_GATE_REPORT.md]
---

# CPT B eval strategy (verified 2026-08-28) — next B spec

Operator approved this as the continue-session spec (nits from fact-check applied). Do **not** create a GPU until that chat says go. Implement in `train_cpt_sota.py` / generator **when training is approved** — none of floor, 16–32 docs, extra buckets, or composite stop exist in code today.

One-liner: **Train on one mix; during B log separate holdout buckets with 16–32 docs (not 2); do not halt before ~0.4 packed epoch; stop only when Spurgeon and mix are both flat within epsilon — not mix-only, not 2-doc Spurgeon-only. Keep C per-bucket as the ship gate.**

## Context (S5) — do not redo
- Train is already one mix (~90M: Spurgeon 40.2%, Puritan 45.7%, confession 5.5%).
- B early-stop 375/4128 (~8.2M, ~9%). Stop key: `eval_spurgeon_loss` on **2** Spurgeon docs (`EVAL_DOCS_PER_BUCKET=2`, T4 VRAM hatch).
- Spurgeon 2.292@25 → **2.254@325** then ±0.005. Mix **2.085 → 2.029**, still falling. Mix val on disk is 520 docs (1% split); B only scored 4.
- C: probe PASS vs Ampere base; §5 −15% FAIL. Adapter SHA256 `ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303`.

## Do not
1. **Mix-only early-stop.** First B `eval keys=['mix']`. Mix **rose** 2.316→2.463 (did not “look OK”). C v3 holdouts +9 / +11.6 / +15.4 / +17.8%. Mix val = `VAL_FRACTION=0.01` random split of train, not C holdouts.
2. **One collapsed “Reformed mix” PPL** (merge Spurgeon/Puritan/confession/general). Hides product vs §5 vs forgetting.
3. **2-doc Spurgeon-only stop.** Too noisy; halted S5 while mix still improved.
4. Fresh 1e-5 from base; rebuild mix; T4 4-bit; overwrite Hub v2 until a new C wins; re-C this S5 adapter.
5. Treat 25M tokens as equal to 40–50% of the epoch (they are not).

## Historical nits (do not repeat the overstated version)
- B v6: **all** buckets rose together (mix 1.890→1.920, spurgeon 2.568→2.607). Not “mix stable + spurgeon rose.” `METRIC_FOR_BEST=eval_spurgeon_loss` is because C scores **holdouts**, not because v6 diverged.
- S5 is the divergence the other way: spurgeon flat, mix falling. Composite + floor is the synthesis of both eras.

## Do this on the next B (code changes)

| Layer | Spec |
|-------|------|
| Training | Same unified mix (`a_output_v3`, SHA256 `23dd3820baa0b657cb6528e4fdf1b2d4813c3cfa7b7c982805b4a7ff34990973`). No rebuild. `one_doc_padded`, r=32, GDN, embed FT. |
| Continue | Load S5 LoRA on Qwen3.5-4B-Base, **new Adam**, body LR ~3e-6–5e-6, emb ~1e-6–2e-6. Cosine over continue `max_steps`. Not HF resume (no optimizer.pt). |
| B in-train eval | Keep **separate** buckets. Minimum mix + spurgeon. Add puritan/confession on 24 GB (`EVAL_BUCKETS_DURING_TRAIN` today is `[spurgeon]` only). |
| Sample size | `EVAL_DOCS_PER_BUCKET` **16–32**, or full bucket. C sizes: spurgeon 50, puritan 20, confession 10, general 10 — cap at `len(ds)`. |
| Early-stop **floor** | Pick **one**: `min_steps` ≈ **0.4–0.5 packed epoch** (~1650–2060 of 4128, ~36–45M tokens). Patience cannot fire before that. |
| Halt rule | **Composite** custom callback (HF EarlyStopping is single-metric). Stop only if Spurgeon **and** mix are both flat/worsening for N evals **within epsilon** (else ±0.005 still fires). Keep `max_steps` = one packed epoch so mix cannot crawl forever. |
| Best ckpt | Separate from halt: keep `METRIC_FOR_BEST=eval_spurgeon_loss` (or a weighted sum). `QuietEarlyStoppingCallback` stays for per-dict log keys. |
| Abort-at-50 | **Off/loosened on this continue** (loss already low). Keep it on any fresh-from-base run. |
| C | Unchanged per-bucket holdouts. Score the **new** adapter vs **its** Ampere base. Export `EXPECTED_ADAPTER_SHA256` (script default is still v2). Keep Hub `…-cpt-lora-v2` until new C wins. |

## Infra (when GPU approved)
Volume `7hb931c5oe` via REST v1 (MCP `create-pod` drops `objectMounts`). Scp optimizer + checkpoints. Community 4090 was empty; Secure US-IL-1 worked. SSH `~/.ssh/runpod_cpt`.
