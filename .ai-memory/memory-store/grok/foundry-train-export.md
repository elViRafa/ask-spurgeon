---
store_path: grok/foundry-train-export
title: "Grok Bot Foundry for train/export code"
summary: "- **Foundry** — write/refine CPT+SFT+export code via Cursor Cloud Agents"
priority: high
tags: [grok, grok-bot, sft, cpt, export, gguf, ollama]
schema_version: 1.3
last_updated: "2026-09-26T15:05:03-03:00"
evidence: [continued_pretrain/GROK_BOT_FOUNDRY.md, .cursor/skills/llm-train-export/SKILL.md, fine_tuning/scripts/sft_export_if_gates.ps1]
---

# Grok Bot Foundry (train + export code)

Created 2026-09-26. Create the Bot in the Grok Bot app from `continued_pretrain/GROK_BOT_FOUNDRY.md`. No create API from Cursor.

## Split
- **Foundry** — write/refine CPT+SFT+export code via Cursor Cloud Agents. Skill: `.cursor/skills/llm-train-export/SKILL.md`.
- **Forge** — Vast/Runpod GPU ops. Skill: `.cursor/skills/gpu-train-ops/SKILL.md`.

## Rules Foundry must keep
- One knob per PR. Dry orchestrator before go.
- No GPU rent, no Hub overwrite, no GGUF upload without operator go.
- SFT export only after `sft_export_if_gates.ps1` (refusal ≥0.85, echo ≤0.02, corrupt 0, im_end stop ≥0.85, leak ≤0.02, groundedness ≥4.0).
- Knowledge Q&A speaker, not Spurgeon persona. No qa_mix_v2 rebuild.
