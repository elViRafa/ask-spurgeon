---
store_path: fine-tuning/vultr-spend-risk-controls
title: "Vultr GATE-0 spend risk controls"
summary: "**Operator intent (2026-09-04):** After Vultr raises Max Instance Cost for Cloud GPU, keep billing risk minimal"
priority: high
tags: [vultr, billing, sft, gate0, risk]
schema_version: 1.3
last_updated: "2026-09-04T08:43:49-04:00"
review_status: stale
---

# Vultr GATE-0 spend risk controls

**Operator intent (2026-09-04):** After Vultr raises Max Instance Cost for Cloud GPU, keep billing risk minimal. Limit increase is a *ceiling*, not auto-spend.

## Facts
- Account had Max Instance Cost **$100/mo**, credit ~$255, max instances 5.
- Target SKU `vcg-a16-12c-128g-32vram` ≈ **$0.94/hr** ≈ **$690/mo** list rate → needs limit ~$700–1000/mo.
- Stopped GPU still bills; only **DELETE** stops charges.
- Forgotten 24h GPU ≈ ~$23.

## Mandatory agent/run rules
1. Prefer **one** short-lived GPU VM; never leave idle.
2. On setup/inject/launch fail → **destroy immediately** (`vultr_destroy.ps1 -Force`).
3. Monitor with `vultr_monitor_until_done.py` (wall clock ≤ **8h**); on done/crash → fetch then **DELETE**.
4. Do **not** create a second GPU while one `sft-gate0` session exists.
5. Do **not** request huge limits beyond ~$700–1000/mo max instance cost unless Vultr requires it.
6. Never log `VULTR_API_KEY` / `HF_TOKEN`.
7. Before provision: confirm no leftover `sft-gate0` / probe instances via API list.
8. Expected successful run budget: ~**$8–12** (8–12h); abort/destroy if stuck past wall clock.

## Operator checklist
- Request limit increase only as needed for Cloud GPU.
- Watch Billing / Remaining Credit during the run.
- If unsure a VM is still needed → destroy.
