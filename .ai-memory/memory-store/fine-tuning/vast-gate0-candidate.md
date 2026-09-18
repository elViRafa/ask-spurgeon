---
store_path: fine-tuning/vast-gate0-candidate
title: "Vast.ai GATE-0 candidate"
summary: "While Vultr GPU is blocked ~30 days, **Vast.ai can run GATE-0** if we rent a reliable SSH GPU and reuse remote scripts (`sft_remote_setup.sh` / merge / train)"
priority: medium
tags: [cost, brl]
schema_version: 1.3
last_updated: "2026-09-05T18:19:51-04:00"
---

# Vast.ai for GATE-0 SFT (candidate)

While Vultr GPU is blocked ~30 days, **Vast.ai can run GATE-0** if we rent a reliable SSH GPU and reuse remote scripts (`sft_remote_setup.sh` / merge / train).

## Fit
- Job: merge Hub CPT LoRA v2 → train qa_mix_v2 SFT LoRA → fetch adapter → destroy.
- Model ~4B + LoRA: **16–24 GB VRAM** enough (4090 preferred).
- Unsloth is first-class on Vast (Studio template exists); we can also use plain CUDA image + our setup.

## Risks / ops
- Spot/interruptible hosts may kill mid-train — prefer high reliability / on-demand if available.
- Pin **torch 2.11** (ScalingType) — do not trust random image torch versions.
- SSH: some Unsloth docker tags conflict with Vast sshd; use stable image or fix on-start.
- Billing: destroy when done; same spend discipline as Vultr risk controls.

## Status
Not implemented yet — no `vast_*.ps1` in repo. Manual rent + SSH + existing `.sh` is enough for one GATE-0 run.

## Cost ballpark BRL (2026-09-05, FX ~R$5.13/USD)

Assumes RTX 4090 ~US$0.30–0.40/hr (Vast median / RunPod community); destroy when done.

| Job | Hours (typical) | USD | BRL (~) |
|-----|-----------------|-----|--------|
| CPT LoRA **merge** alone | 0.5–1.5 (incl setup) | $0.20–0.60 | **R$1–3** |
| GATE-0 **SFT** (+ merge same VM) | 8–12 wall | $2.5–5 (4090) / $8–12 (Vultr A16) | **R$13–26** / **R$41–62** |
| CPT **resume** (S6-style continue B) | 8–16 wall @ 4090 | $2.5–6.5 | **R$13–33** |

Buffers (retries, idle, download): add ~20–50%. Not a quote — live marketplace rates vary.
