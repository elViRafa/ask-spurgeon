---
store_path: pretraining/cpt-hub-s7-overwrite
title: "Hub …-cpt-lora-v2 now S7 s5best SHA 06354dfc"
summary: "Explicit Hub overwrite of private `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` with S7 Phase A **s5best** (step 1200)"
priority: medium
tags: [cpt, hub, s7, lora]
schema_version: 1.3
last_updated: "2026-09-22T17:55:58-03:00"
evidence: [continued_pretrain/scripts/eval_cpt_sota.py, continued_pretrain/scripts/upload_cpt_lora_to_hf.py, continued_pretrain/NEXT_CPT_S7.md]
---

# Hub CPT LoRA overwritten with S7 s5best (2026-09-22)

## Operator approve
Explicit Hub overwrite of private `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` with S7 Phase A **s5best** (step 1200).

## Identity
| Field | Value |
|-------|--------|
| Repo | https://huggingface.co/rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2 (private) |
| SHA256 | `06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432` |
| Local source | `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7/fetch/theology_cpt_lora_s5best/` |
| Train | S7 continue from S6; composite early-stop; s5best @ 1200 |
| C (stack pin) | spurgeon **12.45 (−13.0%)**, puritan 5.52 (−8.6%), confession 5.27 (−6.0%), general 11.95 (−0.8%) |

## Replaced
Previous Hub contents were S6 SHA `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c` (spurgeon 12.85). Still on local disk under `vast_cpt_s6/fetch/`.

## Upload
```
python continued_pretrain/scripts/upload_cpt_lora_to_hf.py \
  --adapter-dir …/theology_cpt_lora_s5best \
  --expected-sha256 06354dfc… \
  --metrics-dir …/vast_cpt_s7_c \
  --commit-message "CPT S7 s5best step-1200 isolation-C…"
```
Also wrote `ADAPTER_SHA256.txt`, metrics, `STACK_PIN.txt` on Hub.

## Not done
- No merge / GGUF
- No public flip
- §5 −15% still FAIL (puritan/confession)

## Code defaults after Hub overwrite
- `eval_cpt_sota.py` / `_gen_sota_notebooks.py` `EXPECTED_ADAPTER_SHA256` default → `06354dfc…`
- `upload_cpt_lora_to_hf.py` adds `EXPECTED_SHA256_S7`; default expected SHA is S7
- `NEXT_CPT_S7.md` Hub line updated to S7
