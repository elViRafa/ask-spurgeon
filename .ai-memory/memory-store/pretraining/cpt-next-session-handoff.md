---
store_path: pretraining/cpt-next-session-handoff
title: "CPT next-session handoff"
summary: "- Dry `vast_cpt_s7_orchestrate.ps1` green (2026-09-28)"
priority: high
tags: [cpt, s7, handoff, p0]
schema_version: 1.3
last_updated: "2026-09-28T08:10:13-03:00"
evidence: [pretraining/cpt-s7-replay-isolation-c-complete, pretraining/cpt-s7-holdout-sibling-replay, pretraining/cpt-hub-keep-phase-a, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_replay/CONTINUE_FROM.json]
summary_hash: 004845cafaef8d06bbbc0f775d2b856d
---

# CPT next-session handoff

## Do next

1. Operator **go** to rent one 4090 (credit ~$5.83).
2. Forge: pack+sync `a_output_v6_p0` + init `0289f1c9` (flat s5best under vast_cpt_s7_replay/fetch), new Adam, session `vast_cpt_s7_p0`.
3. After B: isolation C on P0 holdouts; then destroy pod (save adapter locally first).
4. Hub stays Phase A until C wins Puritan hard (+ Spurgeon keep). Confession soft/monitor.

## Ready now

- Dry `vast_cpt_s7_orchestrate.ps1` green (2026-09-28)
- Mix SHA `ad817213af207428785c4cfac12ddc1bc390b3e59d6e97b43491fafdafe91962`
- Code: `--target-confession-share` in `07_build_theology_mix.py`

## Do not

- Rent without go; overwrite a_output_v6 / v3-v5; HF-resume sota; Hub-push on fail
