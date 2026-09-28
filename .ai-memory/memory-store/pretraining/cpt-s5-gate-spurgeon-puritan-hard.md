---
store_path: pretraining/cpt-s5-gate-spurgeon-puritan-hard
title: "CPT s5: Spurgeon keep + Puritan hard; confession soft"
summary: "Confession is about 9 percent of mix chars vs Puritan about 50 percent and Spurgeon 35 percent, and confession holdouts are only 10 docs"
priority: high
tags: [cpt, s7, gate, confession, puritan]
schema_version: 1.3
last_updated: "2026-09-28T07:25:16-03:00"
---

# CPT section5 gate reframed: Spurgeon keep + Puritan hard; confession soft

## Decision (2026-09-28, LLM training room)
Confession is about 9 percent of mix chars vs Puritan about 50 percent and Spurgeon 35 percent, and confession holdouts are only 10 docs. Do not expect CPT to perfectly reflect confessions in form, or burn GPU chasing confession -15 percent as if it were Spurgeon-scale.

## Gate until mix share is honest
- Spurgeon: keep (do not regress past about 13.3 / stay near best local)
- Puritan: hard section5 target (aim -15 percent vs Ampere base)
- Confession: soft / monitor until confession share or curated mass is honest
- Hub stays Phase A 06354dfc until a gate-pass C under this framing

## Next recipe (P0)
Confession/puritan sibling reweight (one knob), dry vast_cpt_s7_orchestrate.ps1 green, then operator go. Init local 0289f1c9 + new Adam. No commentary flood / Shaw-SSK fetch as first step. No rent until go.
