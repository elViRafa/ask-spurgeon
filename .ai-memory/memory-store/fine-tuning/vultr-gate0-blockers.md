---
store_path: fine-tuning/vultr-gate0-blockers
title: "Vultr GATE-0 blockers"
summary: "- Vultr Cloud GPU is **not viable for GATE-0 for ~30 days** from denial date"
priority: high
tags: [vultr, sft, gate0, blocked, billing]
schema_version: 1.3
last_updated: "2026-09-05T18:03:37-04:00"
---

# Vultr GATE-0 blockers (do not retry GPU until review window)

## What failed
1. **API IP ACL** — agent public IP must be allowlisted (IP changes; last OK: `38.43.106.44`).
2. **Cloud GPU product access** — `POST /instances` for *all* VCG plans (incl. 2GB A16) returned HTTP 400: `Please open a support request for access to this product.`
3. **Max Instance Cost $100/mo** — target `vcg-a16-12c-128g-32vram` ≈ $0.94/hr ≈ $690/mo list; ceiling too low.
4. **Support 2026-09-05** — refused limit increase due to **account age**; review extended **+30 days**. Asked continued usage + positive history before substantial increases.

## Implications
- Vultr Cloud GPU is **not viable for GATE-0 for ~30 days** from denial date.
- Exhaustive probe: 112 plan@region creates → **0 OK** (28 access-denied, 84 not-in-region).
- Scripts/runbook remain ready (`VULTR_RUNBOOK_SFT.md`, `vultr_orchestrate.ps1`); spend-risk rules still apply when GPU unlocks.
- Do **not** burn credit on tiny GPUs or multi-day CPU SFT for this job.

## After 30 days
Re-check Limits + create-probe A16; if OK, re-run orchestrate with destroy-on-done.
