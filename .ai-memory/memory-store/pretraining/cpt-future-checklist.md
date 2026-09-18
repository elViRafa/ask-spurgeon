---
store_path: pretraining/cpt-future-checklist
title: "CPT future session checklist"
summary: "Short CPT resume checklist pointing at cpt-current / cpt-v3-s6-handoff; SFT is separate."
priority: high
tags: [handoff]
schema_version: 1.3
last_updated: "2026-08-29T11:22:29-04:00"
summary_hash: 12369953e99b588bfe506ced27377723
---

## Future CPT quick start

1. Read `pretraining/cpt-current` then `pretraining/cpt-v3-s6-handoff` (+ `s6_session.json` if present).
2. Resume S6: mount volume `7hb931c5oe`, `PREV_RUN_CHECKPOINT=checkpoint-2100`, `CPT_RUN_MODE=fresh`, fix monitor (log completion markers, not SSH-only).
3. New corpus / more tokens: `continued_pretrain/NEXT_CPT_MORE_TOKENS.md` / `CORPUS_V3_S6_CONTINUE_CHECKLIST.md`.
4. C eval: correct `EXPECTED_ADAPTER_SHA256`; compare to Hub v2; keep v2 if worse.
5. Never train without volume verify (`s6_verify_mount.ps1`).

## Parallel track
SFT rewrite / quote gate: `fine-tuning/next-session-handoff`. Do not mix CPT and SFT pods/volumes.
