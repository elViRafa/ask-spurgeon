---
store_path: fine-tuning/sft-gate0-readiness-2026-09-02
title: "SFT GATE-0 readiness revision (2026-09-02)"
summary: "**Date:** 2026-09-02 ~09:30 ET"
priority: high
tags: [sft, runpod, gate0, readiness]
schema_version: 1.3
last_updated: "2026-09-02T09:28:26-04:00"
evidence: [fine_tuning/scripts/merge_cpt_lora.py, fine_tuning/scripts/sft_provision_pod_mcp.py, fine_tuning/scripts/sft_provision_pod.ps1, fine_tuning/scripts/sft_runpod_common.ps1, fine_tuning/scripts/13_sft_local_readiness.py, fine_tuning/RUNPOD_RUNBOOK_SFT.md]
---

**Date:** 2026-09-02 ~09:30 ET
**Verdict:** Data + orchestration are GATE-0 ready locally. GPU launch is **waiting on US-IL-1 capacity** (volume `7hb931c5oe`). Two launch bugs were found and fixed this session.

## Live checks (this session)

| Check | Result |
|-------|--------|
| `13_sft_local_readiness.py --gate0` | PASS after zip repack |
| `audit_qa_mix_quality.py` | quote **52.2%**, teacherish **1579**, caricature **0**, refusal 12.5% live |
| Special tokens | PASS (ChatML atomic; pad is `<\|vision_pad\|>` 248055 — expected, train script remaps pad off `<\|im_end\|>`) |
| Mix zip vs train | Was **stale** (train 09:21, zip 09:08); **repacked** 12.26 MB |
| Pods | 0 (no billing bleed) |
| Volume | `7hb931c5oe` US-IL-1 75 GB |
| Global 4090 stock | High — **not usable**; volume pins US-IL-1 (no instances) |
| SSH key | `~/.ssh/runpod_cpt` present |

## Bugs fixed before GPU

1. **Hub v2 LoRA is private** (HF 401 unauthenticated). Pod env previously had only `PUBLIC_KEY` — merge download would fail on first boot. Now inject `HF_TOKEN` + `HF_HOME` into pod env (runpodctl, REST, MCP paths). Do not log the token.
2. **`merge_cpt_lora.py --preflight` required adapter files before download**, so first-run merge never reached `snapshot_download`. Preflight now downloads (with token) then SHA-checks.
3. **Two capacity watchers** (120s Python 3.14 + 600s) racing the same log. Killed both; restarted **one** 600s watcher on `.venv` Python 3.13 (PID from `sft_start_capacity_watch.ps1`).
4. Readiness now **fails** if zip is older than `qa_mix_train.jsonl`.

## Still not frozen

QA rewrite rotator from 2026-09-01 is **still running** (`rewrite_qa_rotate_providers.py --retry-drops`). Gates already met — further rewrite is optional. If it merges again, **repack the zip** before the watcher syncs. One `--apply` writer remains (parent/child of that rotator).

## Do not

- Touch `/workspace/theology_cpt_lora/` or `/workspace/checkpoints_sota/`
- EXPORT until F §5 gates
- Start a second watcher
