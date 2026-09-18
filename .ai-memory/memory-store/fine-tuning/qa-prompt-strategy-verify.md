---
store_path: fine-tuning/qa-prompt-strategy-verify
title: "QA verify + F5 slice gap report"
summary: "After overlay-safe catechism variants + multiturn merge:"
priority: high
tags: [sft, qa-mix, f5, verification]
schema_version: 1.3
last_updated: "2026-08-30T22:07:13-04:00"
evidence: [fine_tuning/scripts/audit_qa_mix_quality.py, fine_tuning/data/qa_mix_manifest.json]
---

# QA verify — post slice expansion (2026-08-30)

After overlay-safe catechism variants + multiturn merge:

| Metric | Value |
|--------|------:|
| train | 3264 |
| catechism | 241 (7.4%) |
| multiturn | 100 (3.1%) |
| refusal | ~11.6% live / 11.3% manifest |
| quote | 27.9% |
| teacherish | 553 |
| caricature | 0 |
| readiness | PASS |
| system uniqueness | 1 / canonical |

F5 gaps closed enough for slice diversity: catechism near 8%, multiturn in band. Still deferred: full 5–6k teacher bank, GPU.
