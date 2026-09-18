---
store_path: pretraining/cpt-v3-s6-handoff
title: "S6 CPT handoff — resume B, partial C, Hub v2 policy"
summary: "**Last updated:** 2026-08-28"
priority: high
tags: [cpt, s6, runpod, resume, hub-v2, eval]
schema_version: 1.3
last_updated: "2026-08-28T17:25:41-04:00"
---

# S6 continue-B + partial C — handoff for future CPT

**Last updated:** 2026-08-28

## Training status (S6 continue-B)

| Item | Value |
|------|--------|
| Status | **INCOMPLETE** — do not treat as finished B |
| Last step | **2110 / 4128** (~51% of packed epoch) |
| Stop cause | Pod `dxkqi52onre278` deleted after monitor **false positive** (2× SSH timeout → `training_done`) |
| Volume | `7hb931c5oe` (US-IL-1, 75 GB) — **source of truth** |
| Latest ckpt | `checkpoint-2100` (full adapter) |
| HF best ckpt | `checkpoint-2050` — `eval_spurgeon_loss` **2.4987** |
| S5 init backup on volume | `theology_cpt_lora_s5_init_backup` |
| Staged eval adapter | `theology_cpt_lora` may be checkpoint-2050 copy after C eval |

## Resume S6 B (next CPT session)

1. Provision US-IL-1 + volume `7hb931c5oe` at `/workspace` (cu124 image for 12.4 hosts).
2. **Do not** use `CPT_RUN_MODE=continue` for resume — it **ignores** `PREV_RUN_CHECKPOINT`.
3. Resume with HF checkpoint:
   - `[REDACTED_SECRET]`
   - `CPT_RUN_MODE=fresh` (or unset continue)
4. Fix monitor before walk-away: require log completion markers (`4128/4128`, `COMPOSITE EARLY-STOP`, `Saved run config`) — **not** only `running=False` after SSH flake.
5. Single monitor instance; avoid duplicate `s6_monitor_until_done.py` processes.
6. Scripts: `s6_provision_pod_mcp.py`, `s6_inspect_volume.sh`, `s6_remote_continue_b.sh`, `s6_sync_checkpoints.ps1`.

## Partial C eval (2026-08-28)

Evaluated **checkpoint-2050** on pod `snuapq7oqrd8ww` (may terminate when idle).

| Field | Value |
|-------|--------|
| Adapter SHA256 | `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c` |
| Local metrics | `kaggle/runpod_cpt_v3/s6_c_eval/theology_cpt_eval_metrics.json` |
| Holdout PPL (adapter) | spurgeon **13.34**, puritan **5.72**, confession **5.36**, general **11.90** |
| Δ vs base | spurgeon −6.8%, puritan −5.2%, confession −4.4%, general −1.2% |
| MCQ | WSC **72%**, Heidelberg **47.6%** |
| Probes | 6 greedy repetition warnings (informational) |

**Verdict vs Hub v2:** in same ballpark as S5 C; **keep Hub v2** until full S6 B completes and new C clearly wins.

## Reference adapters (SHA256)

| Label | SHA256 (prefix) | Notes |
|-------|-----------------|-------|
| **Hub v2** (production) | `319d17a3…1478` | HF `…-theology-cpt-lora-v2`; do not overwrite without winning C |
| **S5 LoRA** (S6 init) | `ef4df3a3…c303` | `kaggle/runpod_cpt_v3/theology_cpt_lora/` |
| **S6 partial best** (ckpt-2050) | `6aab9194…36f0c` | from interrupted continue-B |
| **Mix corpus v3** | `23dd3820…0973` | `a_output_v3` |

## Hub v2 explained

Published Hugging Face LoRA from CPT **v2** cycle — current production/reference adapter. Local fallback: `kaggle/runpod_cpt_v2/theology_cpt_lora/`. Policy: new CPT (S5/S6/…) must beat v2 Ampere C scorecard before Hub replace.

## Infrastructure lessons

- **cu124 image** on US-IL-1 Secure (CUDA 12.4 hosts); upgrade torch 2.8+cu126 before Unsloth on cu124 image.
- **Monitor false positives** killed a healthy run; sync can fail mid-checkpoint-write (retry later).
- **Disk:** local `s6_continue_b` checkpoints are backup only; safe to prune partial/stale copies.
- **Session file:** `kaggle/runpod_cpt_v3/s6_session.json`

## Docs

- `CORPUS_V3_S6_CONTINUE_CHECKLIST.md`
- `CORPUS_V3_S6_RERUN_SAFE.md`
- `CORPUS_V3_S5_C_CHECKLIST.md` (C eval pattern)
- `RUNPOD_RUNBOOK.md`
