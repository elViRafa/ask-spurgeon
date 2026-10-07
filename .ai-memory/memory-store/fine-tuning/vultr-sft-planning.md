---
store_path: fine-tuning/vultr-sft-planning
title: "Vultr SFT GATE-0 planning"
summary: "**Updated:** 2026-09-03 ~23:00 ET"
priority: high
tags: [vast, sft, gate0]
schema_version: 1.3
last_updated: "2026-09-05T18:04:00-04:00"
evidence: [fine_tuning/VULTR_RUNBOOK_SFT.md, fine_tuning/scripts/vultr_orchestrate.ps1, fine_tuning/scripts/merge_cpt_lora.py, fine_tuning/scripts/sft_remote_setup.sh]
review_status: stale
---

**Updated:** 2026-09-03 ~23:00 ET
**Status:** Scripts implemented. Live GPU run blocked on Vultr API IP allowlist (`159.26.98.242`).

## What landed
- Runbook: `fine_tuning/VULTR_RUNBOOK_SFT.md`
- Orchestration: `vultr_probe_api.ps1`, `vultr_provision.ps1`, `vultr_wait_ssh.ps1`, `vultr_verify_gpu.ps1`, `vultr_sync.ps1`, `vultr_inject_hf_token.ps1`, `vultr_launch.ps1`, `vultr_fetch.ps1`, `vultr_destroy.ps1`, `vultr_orchestrate.ps1`, `vultr_monitor_until_done.py`
- Session/results: `fine_tuning/kaggle/vultr_sft_session.json`, `fine_tuning/kaggle/vultr_sft_gate0/`
- One-shot: `cd fine_tuning\scripts; .\vultr_orchestrate.ps1`
- Attach console VM: `.\vultr_orchestrate.ps1 -SshHost <ip>`

## Train/merge hardening
- `sft_remote_setup.sh`: always install torch 2.11.0+cu126 if missing/old; smoke `ScalingType` + trl + unsloth + CUDA sm_80+; fail closed.
- A16 env: `SFT_GPU_PROFILE=a16`, `CUDA_VISIBLE_DEVICES=0`, `SFT_PER_DEVICE_BATCH=1`, `SFT_GRAD_ACCUM=16` in `.sft_env` + remote train/setup/merge.
- `merge_cpt_lora.py`: GPU Unsloth merge then CPU PEFT `merge_and_unload` on OOM; `--cpu` / `SFT_MERGE_DEVICE=cpu`; tokenizer completeness check.
- Tokenizer: `load_qwen35_tokenizer` handles Unsloth `TokenizersBackend`.
- QA zip: atomic temp write in `12_package_kaggle_qa_mix.py`. Local `13_sft_local_readiness.py --gate0` PASS (3264/153/100).

## GPU pick (unchanged)
`vcg-a16-12c-128g-32vram` blr ~$0.94/hr — **2x16GB** not one 32GB GPU. Destroy after fetch; do not stop.

## Blocker
`GET /v2/account` → 401 Unauthorized IP `159.26.98.242`. Allowlist that IP (or console-create Ubuntu 24.04 GPU and `-SshHost`). Never log `VULTR_API_KEY` / `HF_TOKEN`.

## 2026-09-04 API wait timeout

- `vultr_orchestrate.ps1 -ApiWaitMinutes 45` exited **1** after ~46 min (`ended_at` 2026-09-04T03:48:35Z).
- Cause unchanged: Vultr API **401** `Unauthorized IP address: 159.26.98.242`.
- No instance provisioned; no session file; GATE-0 merge/SFT not started.
- Unblock: allowlist `159.26.98.242` at https://my.vultr.com/settings/#settingsapi , then re-run `.\vultr_orchestrate.ps1` — or console-create Ubuntu 24.04 GPU A16 32vram in blr and `.\vultr_orchestrate.ps1 -SshHost <ip>`.

## 2026-09-04 provision blocked (product access)

- After API allowlist OK (`38.43.106.44`), `POST /instances` for `vcg-a16-12c-128g-32vram` in `blr` returned **HTTP 400**: `Server add failed: Please open a support request for access to this product.`
- Catalog lists the plan in `atl,blr`; smaller A16 VDI slices also listed in blr but are out of scope for GATE-0 (need ~16GB+ usable VRAM).
- Unblock: operator opens Vultr support ticket for Cloud GPU / that product, then re-run `vultr_orchestrate.ps1`.

## 2026-09-04 exhaustive VCG probe

Tried **112** `plan@region` creates across all catalog `type=vcg` plans. **OK=0**.
- 28× `Please open a support request for access to this product` (includes tiniest A16 2GB / A40 2GB)
- 84× `plan is not available in the selected region`

Account has **no Cloud GPU entitlement** yet; switching SKU/region cannot unblock GATE-0 on Vultr until support enables the product.

## Spend risk (operator)

Limit increase ≠ higher bill. Ceiling only. See `fine-tuning/vultr-spend-risk-controls`.
Hard rules: one VM, destroy on fail/done, 8h wall, no idle stop-only, expected ~$8–12 for GATE-0.

## 2026-09-05 Vultr support denial

Support refused Max Instance Cost increase due to **account age**; review extended **+30 days**. Ask continued non-GPU usage + positive history before GPU-eligible limits.

**Implication:** GATE-0 on Vultr Cloud GPU is **not viable for ~30 days**. Prior create probes already failed with product-access 400 even on 2GB A16 (under $100/mo), so staying under current $100 ceiling does not unlock training GPUs.

**Do not** burn credit on tiny useless GPUs or multi-day CPU SFT for GATE-0. Prefer RunPod/other GPU host; optional light Vultr **CPU** usage only if building account history for a later limit ask.

## Alternate host: Vast.ai (candidate for GATE-0 while Vultr blocked)

**Can do the job:** Yes — rent SSH/Docker GPU, run same pipeline (CPT LoRA merge + SFT LoRA). Vast markets Unsloth Studio templates; CLI/SSH custom images also work.

**Hardware:** Prefer **≥16 GB** usable VRAM (RTX 4090 24GB ideal; avoid tiny VDI). Qwen3.5-4B LoRA + merge fits; use CPU PEFT merge fallback if OOM.

**Caveats vs Vultr/RunPod:** Marketplace hosts (pick high reliability); interruptible offers cheaper but can die mid-run; SSH/image quirks (some Unsloth tags break sshd — prefer stable pytorch/cuda image + install our stack); no existing `vultr_*.ps1` — need thin Vast rent/sync/destroy or manual SSH with `sft_remote_*.sh`.

**Stack rule unchanged:** torch **2.11+cu126**, ScalingType smoke, destroy when done, HF_TOKEN for private Hub CPT adapter.
