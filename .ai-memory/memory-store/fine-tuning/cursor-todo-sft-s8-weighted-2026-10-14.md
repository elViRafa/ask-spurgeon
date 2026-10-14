---
store_path: fine-tuning/cursor-todo-sft-s8-weighted-2026-10-14
title: "CURSOR TODO weighted SFT S8 — done on main"
summary: "Completed on main `5b12b79`"
priority: medium
tags: [sft, weighted, todo, forge]
schema_version: 1.3
last_updated: "2026-10-14T11:36:34-03:00"
evidence: ["commit:5b12b79", fine_tuning/scripts/vast_sft_s8_weighted_orchestrate.ps1]
---

# Cursor TODO — weighted SFT S8 (2026-10-14) DONE

Completed on main `5b12b79`. Do not re-open unless a new GPU crash appears.

| Item | Status |
|------|--------|
| Seq 4608 + mask fail-closed + SSH LogLevel | done |
| Copy-ToVastWeighted scp harden / gzip / retry | done |
| Unsloth drop fully-masked | done |
| Residual: verify_gpu EAP, force dataprep, tokenizer hygiene | done |
| Forge/Foundry guide refresh | done |
| pytest + dry + push (no QA data, no rent) | done |

## After (operator / Bots)

Foundry verifies `5b12b79` read-only → Forge dry → Rafael go (credit top-up or `-AllowLowCredit`).
