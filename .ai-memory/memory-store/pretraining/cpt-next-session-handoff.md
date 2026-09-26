---
store_path: pretraining/cpt-next-session-handoff
title: "Phase B done; next is isolation C"
summary: "- `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` = S7 Phase A s5best SHA `06354dfc…`"
priority: high
tags: [cpt, s7, handoff, phase-b, eval-c]
schema_version: 1.3
last_updated: "2026-09-23T16:49:44-03:00"
evidence: [pretraining/cpt-s7-vast-phase-b, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7/fetch/theology_cpt_run_config.json]
---

## Next session — Phase B finished (early-stop 750); run isolation C; Hub stays S7

### Production Hub (unchanged)
- `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` = S7 Phase A s5best SHA `06354dfc…`

### Phase B result
- Vast `52264974` destroyed after fetch.
- COMPOSITE EARLY-STOP @ **750**/955. HF best step **700** SHA `6d003041…`. §5 export step **600** SHA `ddbbee3a…`.
- In-train: spurgeon 2.482 / puritan 1.740 / confession 1.666. Mix-val 2.205 (v5, unseeded).

### Do next
1. Isolation C (torch 2.8 + Unsloth 2026.8.22). Pin `EXPECTED_ADAPTER_SHA256` to nested fetch adapters, not the top-level `06354dfc` folder.
2. Keep Hub S7 until winning C.

### Do not
- Treat top-level `fetch/theology_cpt_lora_s5best/` as the new B adapter (that file is still `06354dfc`).
- Overwrite Hub / v3 / v4. Redraw holdouts. Fetch confession S5.
