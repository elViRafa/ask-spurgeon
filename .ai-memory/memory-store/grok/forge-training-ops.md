---
store_path: grok/forge-training-ops
title: "Grok Bot Forge for Vast/Runpod training"
summary: "Create the teammate in the Grok Bot app from `continued_pretrain/GROK_BOT_FORGE.md`"
priority: high
tags: [grok, grok-bot, vast, runpod, sft, training-ops]
schema_version: 1.3
last_updated: "2026-10-14T11:36:49-03:00"
evidence: ["commit:5b12b79", continued_pretrain/GROK_BOT_FORGE.md, .cursor/skills/gpu-train-ops/SKILL.md, fine_tuning/NEXT_SFT_S8_WEIGHTED.md]
---

# Grok Bot Forge (training ops)

Create the teammate in the Grok Bot app from `continued_pretrain/GROK_BOT_FORGE.md`. No create API from Cursor.

## Profile
- **Name:** Forge
- **Title:** Vast / Runpod training watch
- **Job:** Watch/launch CPT+SFT on Vast (primary) and Runpod (secondary). Never train on the Bot computer.

## Current job (2026-10-14)
- Weighted SFT on S8 merged CPT — runbook `fine_tuning/NEXT_SFT_S8_WEIGHTED.md`
- Orchestrator: `fine_tuning/scripts/vast_sft_s8_weighted_orchestrate.ps1`
- Skill: `.cursor/skills/gpu-train-ops/SKILL.md`
- Seq 4608 / peft / `SFT_EXPORT=0`. Hub LoRA v2 `06354dfc` stays.
- Harden on main `5b12b79`. No GPU rent until operator says **go**.
- Auto-destroy only after fetch, or idle >20 min with no train (do not destroy mid-`sft_remote_setup`).

## Operator create / refresh steps
1. Grok Bot → edit Forge profile from updated `GROK_BOT_FORGE.md`
2. Sign into cloud.vast.ai and console.runpod.io (no keys in chat)
3. Paste the first-message block (audit only), then dry before go
