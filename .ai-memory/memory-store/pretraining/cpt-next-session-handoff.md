---
store_path: pretraining/cpt-next-session-handoff
title: "CPT next-session handoff"
summary: "P1 dry READY; PR #6 merge + go then rent vast_cpt_s7_p1"
priority: high
tags: [cpt, s7, handoff, p1]
schema_version: 1.3
last_updated: "2026-10-02T18:15:00-03:00"
evidence: [pretraining/cpt-s7-p1-metric-puritan, pretraining/cpt-s7-p0-confession-reweight, pretraining/cpt-hub-keep-phase-a]
---

# CPT next-session handoff

## Do next

1. Merge [PR #6](https://github.com/elViRafa/ask-spurgeon/pull/6) to main.
2. Operator **go** to rent one 4090.
3. Forge: `.\vast_cpt_s7_orchestrate.ps1 -Go -StartMonitor` — reuse pack `a_output_v6_p0`, init `a70fded8`, session `vast_cpt_s7_p1` / label `cpt-s7-p1`.
4. Train+C → fetch → destroy. No Hub. No second GPU.

## Ready now

- Dry `vast_cpt_s7_orchestrate.ps1` READY (2026-09-28)
- Knob: `metric_for_best=eval_puritan_loss` (Spurgeon stays in composite abort)
- Mix SHA `ad817213af207428785c4cfac12ddc1bc390b3e59d6e97b43491fafdafe91962`
- Branch commit `25e14c2` on `cpt-s7-p1-metric-puritan`

## Do not

- Rent without go; overwrite a_output_v6 / v3-v5; HF-resume sota; Hub-push on fail; heuristic dream that redacts continue-from marker paths
