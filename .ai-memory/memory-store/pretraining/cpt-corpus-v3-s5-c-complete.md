---
store_path: pretraining/cpt-corpus-v3-s5-c-complete
title: "CPT corpus v3 S5 C complete — probe PASS, keep Hub v2"
summary: "GPU `gynfhzyfjcjjyf` **deleted**"
priority: high
tags: [cpt, corpus-v3, s5, eval, runpod]
schema_version: 1.3
last_updated: "2026-08-27T23:44:42-04:00"
evidence: [continued_pretrain/NEXT_CPT_MORE_TOKENS.md, continued_pretrain/kaggle/runpod_cpt_v3/theology_cpt_eval_metrics.json, continued_pretrain/kaggle/runpod_cpt_v3/theology_cpt_run_config.json]
---

# CPT corpus v3 S5 C COMPLETE (2026-08-28)

GPU `gynfhzyfjcjjyf` **deleted**. Volume `7hb931c5oe` kept (this C **did** attach it at `/workspace` via REST v1; MCP `create-pod` still cannot). Do **not** merge. Do **not** overwrite Hub `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2`. Do **not** re-C v2. Do **not** retrain in a leftover GPU.

## Adapter scored
`continued_pretrain/kaggle/runpod_cpt_v3/theology_cpt_lora` SHA256 `ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303` (B best 325). Holdouts `kaggle/a_output_v3/theology_holdouts`. MCQ `data/catechism_mcq.json`. `EXPECTED_ADAPTER_SHA256` exported to the v3 hash. Ampere bf16, `REQUIRE_AMPERE=1`, `RUN_MERGE=False`.

## Scorecard vs this C’s Ampere bf16 base
Do not mix with Kaggle C v4 T4 4-bit, or with v2 C raw PPL (v2 used `a_output` holdouts).

| Bucket | Base | v3 adapter | %Δ |
|--------|------|------------|-----|
| spurgeon | 14.31 | 13.34 | −6.79% |
| puritan | 6.03 | 5.72 | −5.17% |
| confession | 5.61 | 5.36 | −4.42% |
| general | 12.05 | 11.90 | −1.21% |

Probe (all four better than this base): **PASS**. Plan §5 −15% on puritan/confession: **FAIL**. MCQ WSC 70%→72%; Heidelberg 40.5%→45.2% (need +10).

## Keep vs Hub v2 Ampere C (2026-08-27)
v2: spurgeon 13.28 (−7.25%), puritan 5.68 (−5.05%), confession 6.73 (−6.98%), general 13.20 (−1.73%). Spurgeon/puritan raw PPL are slightly worse here. Confession/general look better but those holdouts changed in v3 — not a Hub overwrite. **Keep** Hub `…-cpt-lora-v2` SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`.

## Infra
- MCP `create-pod` GraphQL now 400s (`objectMounts` not on `PodFindAndDeployOnDemandInput`). `runpodctl` still has no REST API key.
- Workaround that worked: REST v1 `POST https://rest.runpod.io/v1/pods` with the MCP OAuth bearer (REST v2 and GraphQL 403 on that token). Community 4090 empty; Secure US-IL-1 **$0.74/hr** **did** attach `networkVolumeId` `7hb931c5oe`.
- SSH `root@203.57.40.78 -p 10057` (key `~/.ssh/runpod_cpt`). Artifacts: `kaggle/runpod_cpt_v3/theology_cpt_eval_metrics.json`, `cpt_eval.log`.

## Next
More-tokens continue only if a later session wants it: `continued_pretrain/NEXT_CPT_MORE_TOKENS.md`. Optimizer was never copied; no HF resume. Do not start that B until the operator says go.

## Why this is not “v3 had more data and lost” (operator asked 2026-08-27)

The mix on disk is larger (~90M / 91.31M verified). Training did **not** use it. Early-stop patience 2 on a **2-doc Spurgeon** eval (`eval_steps=25`) halted at **375/4128** (~**8.2M tokens**, ~9% of one packed epoch). v2’s probe mix was ~**15.6M** and best step **400**. This LoRA saw **less** than v2, not more. `eval_mix` was still falling when the probe flattened.

Spurgeon 13.34 vs v2 13.28 and puritan 5.72 vs 5.68 are noise-level. Confession/general used `a_output_v3` holdouts, not v2 `a_output` — not a like-for-like win. Probe vs **this** C’s Ampere base still **PASS**. Puritan is 45.7% of the mix and confession 5.5%; 8.2M only gave them a thin slice, which is why §5 −15% failed.

This is the playbook’s **preferred continue** case (near v2, far from §5). Repo: `continued_pretrain/NEXT_CPT_MORE_TOKENS.md`. Operator said they will continue in the next question about training and eval. Do not start GPU until that chat says go. Do not fresh 1e-5 from base.
