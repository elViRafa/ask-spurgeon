---
store_path: grok/forge-training-ops
title: "Grok Bot Forge for Vast/Runpod training"
summary: "- **Title:** Vast / Runpod training watch"
priority: high
tags: [grok, grok-bot, vast, runpod, cpt, training-ops]
schema_version: 1.3
last_updated: "2026-09-26T14:27:32-03:00"
evidence: [continued_pretrain/GROK_BOT_FORGE.md, .cursor/skills/gpu-train-ops/SKILL.md, continued_pretrain/NEXT_CPT_S7.md, pretraining/cpt-next-session-handoff]
---

# Grok Bot Forge (training ops)

Created 2026-09-26. There is no API to create a Grok Bot from Cursor. The teammate is created in the Grok Bot app from `continued_pretrain/GROK_BOT_FORGE.md`.

## Profile
- **Name:** Forge
- **Title:** Vast / Runpod training watch
- **Job:** Watch/launch CPT+SFT on Vast (primary) and Runpod (secondary). Never train on the Bot computer.

## Alignment
- Cursor / Cloud Agent skill: `.cursor/skills/gpu-train-ops/SKILL.md`
- Current CPT: v6 replay from nested `ddbbee3a`, session `vast_cpt_s7_replay`, Hub stays Phase A `06354dfc`
- No GPU rent until operator says **go**
- Auto-destroy only after fetch, or idle >20 min with no train

## Operator create steps
1. Grok Bot → New → Create new Bot
2. Paste profile from `GROK_BOT_FORGE.md`
3. Sign into cloud.vast.ai and console.runpod.io (no keys in chat)
4. Paste the first-message block (audit only)
