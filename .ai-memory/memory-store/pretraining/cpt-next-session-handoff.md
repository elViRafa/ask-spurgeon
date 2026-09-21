---
store_path: pretraining/cpt-next-session-handoff
title: "Next session: S6 LoRA good; Hub overwrite needs approve"
summary: "S6 SHA `6aab…` on Unsloth 2026.8.22 / torch 2.8: spurgeon **12.85 (−10.2%)**"
priority: high
tags: [cpt, s6, handoff]
schema_version: 1.3
last_updated: "2026-09-20T19:04:21-03:00"
evidence: [pretraining/cpt-s6-c-eval-regression-diagnosis]
---

# Next session — after stack-isolation flip

S6 SHA `6aab…` on Unsloth 2026.8.22 / torch 2.8: spurgeon **12.85 (−10.2%)**. Vast +27.9% was **eval-stack false FAIL**. See `pretraining/cpt-s6-stack-isolation-c`.

## Do
1. Keep Hub v2 until operator **explicitly** approves overwrite (S6 beats Hub v2 13.28 on this scorecard but overwrite is a separate session).
2. Prefer confirmatory Runpod C of same SHA when Runpod has funds (this C was Vast host + S5 software pin).
3. Optional: Hub overwrite of `…-theology-cpt-lora-v2` with nested `6aab…` after approve.
4. Do **not** start a blind continue-B to “fix C”.

## Do not
- Treat Vast C 18.31 as ground truth for these weights
- Merge / Hub overwrite without operator go
- Re-rent Vast C on torch 2.11 / Unsloth 2026.9.x for this SHA

## Paste
```
S6 stack-isolation: SHA 6aab on Unsloth 2026.8.22/torch 2.8 → spurgeon 12.85 (−10.2%).
Vast +27.9% was false FAIL. Hub overwrite needs separate approve.
```

## Clarification (side-chat 2026-09-20)
- False FAIL was **C stack**, not “B early-stop was wrong because of C”.
- C artifact = ckpt-**2050** / SHA `6aab…` (stop was 2400; ignore 2400 adapters).
- S6@2050 beats Hub v2 on PPL scorecard; overwrite still explicit approve only.
