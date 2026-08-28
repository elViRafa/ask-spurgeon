# CPT v2 — Kaggle pipeline status (handoff)

Last updated: **2026-08-27** (S2 mix done; **next = S3**; LoRA on **private Hub**; Runpod C COMPLETE; GPU deleted; Kaggle STOP; **no train until approved**)

## Stopped here (read first)

**Runpod C COMPLETE** (2026-08-27). Community RTX 4090 Ampere bf16, adapter SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478` (B best ckpt-400). Metrics: [`kaggle/runpod_cpt_v2/theology_cpt_eval_metrics.json`](kaggle/runpod_cpt_v2/theology_cpt_eval_metrics.json). **GPU `rf2dayesihddon` deleted.** `RUN_MERGE=False`.

**Probe bar PASS:** all four holdout PPLs **better than this run’s bf16 base** (spurgeon −7.2%, puritan −5.0%, confession −7.0%, general −1.7%). Ampere + embed LoRA + `one_doc_padded` **stopped hurting** the base (C v4 was uniform ~+2%).

**§5 −15% still FAIL** (puritan/confession need ≥15% better). Do **not** merge. Compare %Δ vs **this C’s base**, not C v4 T4 4-bit PPL numbers.

**Kaggle `rafaelvieira1` remains STOP** (B v14 ERROR). Mix **S2 rebuilt** (weight **0.9310**, keep-all ON, **86.18M** tokens). **Next = S3.** Volume `7hb931c5oe` (US-IL-1) still unused (MCP cannot attach it). **Do not train until approved.**

Full plan: memory `pretraining/cpt-v2-runpod-two-session-plan`.

Prior Kaggle COMPLETE B: **v12** (eval rose). Last C **v4 §5 FAIL** on B v6 ckpt-25.

| Question | Answer |
|----------|--------|
| Kaggle B | **v14 ERROR** — STOP this user |
| Last COMPLETE B | **Runpod 2026-08-27** (best step **400**; SHA256 `319d17a3…1478`) |
| Last live C | **Runpod C 2026-08-27** / probe PASS, §5 FAIL (Ampere bf16 vs own base) |
| Next work | **S2 mix done. Next = S3** (Wave 3 scarce + capped commentary). **Do not train until approved.** Do not merge. Keep Hub LoRA as fallback. Kaggle stays STOP. Handoff: [`CORPUS_V3_S3_HANDOFF.md`](CORPUS_V3_S3_HANDOFF.md) |
| Mix rebuilt? | **Yes (S2)** — weight **0.9310**, keep-all ON (other 1.074), **86.18M** tokens, **48841** docs, **295.1M** chars. Henry exposition excluded |
| Runpod | **0 pods**; volume `7hb931c5oe` unused; C metrics local |

## Saved LoRA snapshot (keep)

Documented adapter if a later run never beats it. **Not merged.**

- Card + load instructions: [`kaggle/runpod_cpt_v2/theology_cpt_lora/README.md`](kaggle/runpod_cpt_v2/theology_cpt_lora/README.md)
- Session results: [`kaggle/runpod_cpt_v2/SESSION_RESULTS.md`](kaggle/runpod_cpt_v2/SESSION_RESULTS.md)
- Snapshot index: [`kaggle/runpod_cpt_v2/README.md`](kaggle/runpod_cpt_v2/README.md)
- SHA256 `adapter_model.safetensors`: `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`
- Weights (~1.45 GB) stay on disk (gitignored). **Private Hub copy:** https://huggingface.co/rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2

## One-line status

**Kaggle STOP (v14 ERROR).** Runpod B **COMPLETE** (best 400). Runpod C **COMPLETE**: holdout PPL beats Ampere bf16 base (spurgeon −7.2%). §5 −15% still miss. LoRA kept locally + private Hub. **Do not merge.** GPU deleted.

## Corpus expansion (done)

| Metric | Before | After |
|--------|--------|-------|
| Raw Puritans on disk | ~18 MB | **~34.4 MB** |
| Mix train chars | ~27.4M | **~51.5M** |
| Verified tokens (Qwen3.5) | ~8.2M | **~15.6M** |
| Docs | 4401 | **8245** |
| Spurgeon weight | 0.087 | **0.164** (subsamples ~84% of Spurgeon) |
| Shares | S40.5 / P40.9 / C5 / B3.6 / G10 | **same targets held** |

Manifest: [`data/theology_mix_manifest.json`](data/theology_mix_manifest.json) — **not rebuilt this session.**

Source of truth: [`scripts/_gen_sota_notebooks.py`](scripts/_gen_sota_notebooks.py) (regen notebooks; do not dual-edit ipynb).

## Recipe / B training

| Check | Result |
|-------|--------|
| A data prep | COMPLETE on expanded corpus |
| B v4 | FAIL — `formatting_func` on text eval |
| B v5 | FAIL — CUDA OOM (batch 2 + embed LoRA) |
| **B v6** | **COMPLETE** — batch 1×16, no embed LoRA, **stream** pack, best=step 25 |
| **C v4** | **COMPLETE / §5 FAIL** — scored B v6 `theology_cpt_lora` == **checkpoint-25** |
| B v7–v10 | FAIL — eval OOM; `float!=Half` lm_head; disk full at ckpt-75 |
| **B v11** | **COMPLETE** — LR **2e-5**. Early-stop **75**; eval **rose** 2.349→2.363→2.383; best=**25** |
| **B v12** | **COMPLETE** — LR **1e-5**. Early-stop **75**; eval **rose** 2.340→2.345→2.361; best=**25**; SHA256 `ffe193…886a` |
| **B v13** | **ERROR** — D1/D2 PASS (`multi_doc_rows=0`, 10779 rows); kernel died ~ckpt-100 (~3 h) |
| **B v14** | **ERROR** — resume missed (`No prior checkpoint found`); fresh from 0; same death window. **STOP Kaggle** |
| **Runpod B** | **COMPLETE** — 4090 bf16 + embed LoRA; D1/D2 PASS; abort-at-50 pass; early-stop **450**; best **400** (`eval_spurgeon` 2.288→2.248) |
| **Runpod C** | **COMPLETE** — probe PPL beats own bf16 base (all 4 buckets); §5 −15% miss; `RUN_MERGE=False` |

## Other causes of poor CPT (beyond 819k tokens / frozen embeds)

Uniform ~+2% PPL on every domain bucket = adapter **hurt** the base, not “underfit but harmless.” Full write-up: memory `pretraining/cpt-v2-additional-failure-modes`.

| Severity | Issue | Still broken after this session? |
|----------|--------|---------------------------|
| High | LoRA drift by step 25 (v6/v11/v12) | **Runpod B+C:** eval_spurgeon fell in B; C holdout PPL **beats** Ampere bf16 base |
| High | Packed 2048 train vs C prefix-only PPL | **v13/v14** one_doc_padded (`multi_doc_rows=0`); Runpod uses the same pack |
| Medium | Qwen3.5 float32-on-4bit hybrid | **T4 path only.** Ampere bf16 now enabled even with embed LoRA |
| Medium | Spurgeon weight **0.164** undersamples ~84% | **Code path added**; mix **not** rebuilt |
| Medium | Tiny holdouts | **Yes** |
| Medium | §5 −15% bar sized for ~110M-token CPT | **Yes** |

## C v4 §5 scorecard (decisive)

Positive Δ = worse than base.

| Bucket | Base | v2 | %Δ | Gate | Result |
|--------|------|-----|-----|------|--------|
| spurgeon | 14.94 | 15.24 | +2.0% | better than base | **FAIL** |
| puritan | 6.20 | 6.34 | +2.2% | ≥15% better | **FAIL** |
| confession | 7.78 | 7.93 | +1.9% | ≥15% better | **FAIL** |
| general | 14.07 | 14.61 | +3.8% | ≤10% worse | **PASS** |

MCQ: WSC 70%→76% (+6); Heidelberg 38.1%→42.9% (+4.8, need +10).

## Runpod C scorecard (Ampere bf16, 2026-08-27)

Compare %Δ vs **this run’s bf16 base**, not C v4 4-bit PPL. Negative Δ = better than base. Adapter SHA256 `319d17a3…1478`.

| Bucket | Base PPL | v2 PPL | %Δ | Probe (beat base) | §5 |
|--------|----------|--------|-----|-------------------|-----|
| spurgeon | 14.31 | 13.28 | −7.2% | **PASS** | better-than-base **PASS** |
| puritan | 5.99 | 5.68 | −5.0% | **PASS** | ≥15% better **FAIL** |
| confession | 7.24 | 6.73 | −7.0% | **PASS** | ≥15% better **FAIL** |
| general | 13.43 | 13.20 | −1.7% | **PASS** | ≤10% worse **PASS** |

MCQ: WSC 70%→74% (+4); Heidelberg 40.5%→45.2% (+4.7, need +10). Probes still show repetition (informational).

**Verdict:** probe success (stopped hurting; all buckets better). **Do not merge** until §5 −15% (or an explicit decision to ship LoRA anyway).

## Current pipeline table

| Stage | Status | Notes |
|-------|--------|-------|
| Local corpus + mix | **S1 done** | weight 0.6586 / 57.60M tok. Next = **S2 fetch**. keep-all Spurgeon **not** applied |
| Kaggle `theology-cpt-corpus` | Updated | 2026-08-25 (old subsample mix) |
| A → `theology-cpt-dataset` | Updated | 8162 train / 83 val |
| B training | **Runpod COMPLETE** | best step 400; Kaggle v14 still ERROR / STOP |
| C eval | **Runpod COMPLETE** | probe PPL beats bf16 base; §5 −15% miss. C v4 still FAIL on B v6 |
| CPT merge / public HF | **Blocked** | §5 −15% not met. **Private** LoRA backup exists (see snapshot) |
| Runpod | **C done; GPU deleted** | metrics at `kaggle/runpod_cpt_v2/`; volume `7hb931c5oe` empty |

## Next session actions

1. **S3** — Wave 3 scarce + capped Hodge/Calvin commentary (10–15 MB combined). Do not grow Puritan treatise mass (confession share 1.8%). See [`CORPUS_V3_S3_HANDOFF.md`](CORPUS_V3_S3_HANDOFF.md).
2. **Do not train** / start B/C until approved. Do **not** merge. Do not push Kaggle. Do not overwrite Hub LoRA. Do not re-C the keepable adapter.
3. Next GPU (only after S5 approval): attach volume `7hb931c5oe` via **runpodctl** + `RUNPOD_API_KEY` (MCP still cannot attach).
4. Kaggle remains STOP. Do not resume 4-bit ckpts onto bf16.

Memory: `pretraining/cpt-corpus-v3-s2-complete`, `pretraining/cpt-corpus-v3-s3-handoff`, `pretraining/cpt-v2-lora-snapshot`.

## URLs

- [B training / log](https://www.kaggle.com/code/rafaelvieira1/theology-cpt-v2-b-training-sota/log)
- [C eval](https://www.kaggle.com/code/rafaelvieira1/theology-cpt-v2-c-eval-sota)
- [Corpus dataset](https://www.kaggle.com/datasets/rafaelvieira1/theology-cpt-corpus)
- [HF dataset](https://www.kaggle.com/datasets/rafaelvieira1/theology-cpt-dataset)

## Agent memory paths

- `pretraining/cpt-v2-session-2026-08-27-results` (**this day’s scorecard + Hub**)
- `pretraining/cpt-v2-next-session-handoff` (**primary next** — merge blocked; mix/tokens decision)
- `pretraining/cpt-v2-lora-snapshot`
- `pretraining/cpt-v2-c-eval-runpod-complete` (C scorecard + SHA256)
- `pretraining/cpt-v2-c-eval-runpod-prep`
- `pretraining/cpt-v2-runpod-b-complete` (B metrics + SHA256)
- `pretraining/cpt-v2-runpod-mcp-volume-gap` (MCP drops `networkVolumeId`)
- `pretraining/cpt-v2-runpod-two-session-plan`
- `pretraining/cpt-v2-runpod-prep-done`
- `pretraining/cpt-v2-runpod-two-session-plan`
- `pretraining/cpt-v2-one-doc-padded`
- `pretraining/cpt-v2-qwen35-upstream-recipes`
- `pretraining/cpt-v2-additional-failure-modes`
- `pretraining/cpt-v2-c-eval-gate-verdict`
- `pretraining/bugs/b-training-sota-known-issues`
- `pretraining/cpt-corpus-expansion-2026-08`

## Paste for new chat

```
Next session = CPT v2 after Runpod C. Do NOT merge. Do NOT re-C this adapter.
Keepable LoRA + usage: continued_pretrain/kaggle/runpod_cpt_v2/README.md
Read: memory pretraining/cpt-v2-session-2026-08-27-results
      continued_pretrain/CPT_V2_KAGGLE_STATUS.md
      continued_pretrain/kaggle/runpod_cpt_v2/SESSION_RESULTS.md
Kaggle B v14 ERROR STOP. Mix 0.164.
Runpod C COMPLETE (community 4090 Ampere bf16): holdout PPL vs own base
  spurgeon -7.2%, puritan -5.0%, confession -7.0%, general -1.7%. Probe PASS. §5 -15% FAIL.
Adapter SHA256 319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478
Private Hub: rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2
GPU deleted. Volume 7hb931c5oe unused. RUN_MERGE=False.
```
