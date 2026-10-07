---
store_path: grok/s8-forge-launch-review
title: "S8 Forge launch review"
summary: "S8 Forge finished the right recipe after two bad starts"
priority: medium
tags: [grok, forge, cpt, s8, launch-guards]
schema_version: 1.3
last_updated: "2026-10-05T16:35:22-03:00"
evidence: [continued_pretrain/scripts/vast_cpt_s8_mhi_continue_remote.sh, continued_pretrain/scripts/vast_cpt_s8_sweep_remote.sh]
---

# S8 Forge launch review

S8 Forge finished the right recipe after two bad starts. First m_lo ran notebook defaults (stock base, r=32, lr 1e-5) because the sweep plan crashed on Path.parents[2] when the file lived in /workspace, and the launcher still started train. A live indent patch of train_cpt_sota.py failed once. The second relaunch trained m_lo, m_hi, and f_hi correctly (m_hi r=128, merged a70, lr 5e-5, 400 steps) and reported SWEEP_STILL_FLAT. No Hub. Fetch skipped optimizer state.

Fixed before the next go, 2026-10-05 afternoon:

- Repo lookup is only inside readiness. --emit and --emit-arm succeed from a one-level /workspace copy.
- Continue and sweep remotes exit if emit fails or is empty. They no longer eval an empty command and then train.
- Continue remote checks the floor recipe and prints RECIPE_OK before train.
- Forge paste: kill on config mismatch or a cosine fallback. Do not edit scripts on the pod. Fetch optimizer files. The Unsloth TRL-patch warning is a status note, not a hotfix.
