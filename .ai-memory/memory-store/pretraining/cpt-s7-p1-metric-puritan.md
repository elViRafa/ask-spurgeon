---
store_path: pretraining/cpt-s7-p1-metric-puritan
title: "S7 P1 metric_for_best=eval_puritan_loss ready"
summary: "PR #6 open; dry READY; init a70fded8; session vast_cpt_s7_p1; wait merge+go"
priority: high
tags: [cpt, s7, p1, metric-for-best, puritan]
schema_version: 1.3
last_updated: "2026-10-02T18:15:00-03:00"
evidence: [continued_pretrain/scripts/cpt_runtime.py, continued_pretrain/scripts/vast_cpt_s7_common.ps1]
---

# CPT P1 — metric_for_best=eval_puritan_loss

One-knob after P0 section-5 FAIL. Same pack; change only best-checkpoint metric.

- `metric_for_best=eval_puritan_loss` (env `METRIC_FOR_BEST`); Spurgeon remains in composite early-stop/abort
- Init: P0 best `a70fded8` (checkpoint-600) + new Adam
- Pack: `mix_v6_p0` / `a_output_v6_p0` SHA `ad817213` (reuse — skip multi-hour scp when possible)
- Session/label: `vast_cpt_s7_p1` / `cpt-s7-p1`
- Branch: `cpt-s7-p1-metric-puritan` @ `25e14c2`
- PR: https://github.com/elViRafa/ask-spurgeon/pull/6 (OPEN, MERGEABLE as of 2026-10-02)
- Proof: pytest prepare+continue 9 passed; dry orchestrate READY
- Go: after merge, `.\vast_cpt_s7_orchestrate.ps1 -Go -StartMonitor` — train+C → fetch → destroy; no Hub
