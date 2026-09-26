---
store_path: pretraining/cpt-hub-s6-overwrite
title: "Hub …-cpt-lora-v2 now S6 SHA 6aab (operator approved)"
summary: "Explicit Hub overwrite of private `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` with S6 ckpt-2050 LoRA"
priority: medium
tags: [cpt, hub, s6, lora, overwrite]
schema_version: 1.3
last_updated: "2026-09-21T10:13:38-03:00"
---

# Hub CPT LoRA overwritten with S6 best (2026-09-21)

## Operator approve
Explicit Hub overwrite of private `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` with S6 ckpt-2050 LoRA.

## Identity
| Field | Value |
|-------|--------|
| Repo | https://huggingface.co/rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2 (private) |
| SHA256 | `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c` |
| Local source | `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/fetch/theology_cpt_lora/theology_cpt_lora/` |
| Train best | HF checkpoint-2050, `eval_spurgeon_loss=2.4987` |
| C (stack pin) | spurgeon **12.85 (−10.2%)** vs base 14.31 — `pretraining/cpt-s6-stack-isolation-c` |

## Replaced
Previous Hub contents were CPT v2 best-400 SHA `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478` (spurgeon 13.28). Still on local disk under `kaggle/runpod_cpt_v2/theology_cpt_lora/`.

## Upload
`python continued_pretrain/scripts/upload_cpt_lora_to_hf.py --adapter-dir …/theology_cpt_lora/theology_cpt_lora --expected-sha256 6aab… --metrics-dir …/stack_isolation_c`
Also wrote `ADAPTER_SHA256.txt` on Hub. `eval_cpt_sota.py` / `_gen_sota_notebooks.py` default `EXPECTED_ADAPTER_SHA256` now **6aab…**.

## Not done
- No merge / GGUF
- No public flip
- No new B
- §5 −15% still FAIL on isolation C
