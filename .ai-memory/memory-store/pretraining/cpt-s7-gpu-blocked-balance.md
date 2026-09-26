---
store_path: pretraining/cpt-s7-gpu-blocked-balance
title: "S7 Phase A GPU blocked: Runpod balance"
summary: "- `a_output_v3` mix SHA `23dd…`"
priority: high
tags: [cpt, s7, runpod, blocker, balance]
schema_version: 1.3
last_updated: "2026-09-22T09:31:17-03:00"
evidence: [continued_pretrain/NEXT_CPT_S7.md, continued_pretrain/scripts/s7_remote_continue_b.sh]
---

# S7 Phase A GPU go blocked — Runpod balance (2026-09-22)

Operator said go. Prep remains ready. **No pod created** (`list-pods` empty).

## Evidence this session
1. `create-network-volume` EU-RO-1 75GB → **400**: account must have **≥ $5**.
2. Secure RTX 4090 EU-RO-1 → **400** no stock (LOW evaporated).
3. Secure L4 (EU-RO-1 / EUR-IS-1 / US-MO-2) with persistent `/workspace` → **402** balance too low to rent a pod.
4. Network volumes on account: **0**. Prior volume `7hb931c5oe` still gone.
5. `runpodctl user` → `no_credentials` (`RUNPOD_API_KEY` unset; `~/.runpod/config.toml` apikey empty). MCP OAuth works for infra CRUD only.

## Local artifacts ready
- `a_output_v3` mix SHA `23dd…`
- Nested S6 LoRA SHA `6aab…` at `kaggle/runpod_cpt_v3/vast_cpt_s6/fetch/theology_cpt_lora/theology_cpt_lora/`
- Launch: `scripts/s7_remote_continue_b.sh`; monitor `-TotalSteps 2064`
- SSH key registered: `runpod-cpt-v2` (matches `~/.ssh/runpod_cpt.pub`)

## On next go (after funds)
1. Add Runpod balance (enough for volume gate ≥$5 + ~$0.50–0.74/hr × expected B hours).
2. Prefer: create network volume in GPU DC, then Secure pod (4090 / L4 / A100) with mount `/workspace`.
3. Optionally set `RUNPOD_API_KEY` for runpodctl `send`/`receive`; else scp via registered SSH key.
4. Sync a_output_v3 + nested 6aab LoRA + train/eval + s7 launchers; `bash s7_remote_continue_b.sh`.
5. Do **not** HF-resume sota; keep Hub S6 until winning C.
