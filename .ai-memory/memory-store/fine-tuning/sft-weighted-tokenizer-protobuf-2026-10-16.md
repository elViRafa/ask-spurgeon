---
store_path: fine-tuning/sft-weighted-tokenizer-protobuf-2026-10-16
title: "Weighted SFT run 8 tokenizer protobuf and mistral-regex"
summary: "Run 8 (evidence evidence_20261016_162847) passed pins and CUDA, then all 3 GPU smokes died in train_sft_sota dataprep"
priority: high
tags: [sft, weighted, vast, protobuf, tokenizer]
schema_version: 1.3
last_updated: "2026-10-16T18:10:36-03:00"
evidence: ["commit:c37601767f552012f94a1d47f71336178369fa5a", fine_tuning/scripts/sft_tokenizer_cpu_smoke.py, fine_tuning/kaggle/vast_sft_s8_weighted/evidence_20261016_162847/capture.txt]
---

Run 8 (evidence evidence_20261016_162847) passed pins and CUDA, then all 3 GPU smokes died in train_sft_sota dataprep. transformers 5.5 _patch_mistral_regex called tokenizer.backend_tokenizer (AttributeError). The except handler then raised ImportError because protobuf was not installed. The broad except ImportError retried AutoTokenizer with fix_mistral_regex=True and hid the first error.

Sep 6 freeze pins are protobuf==7.36.1 and sentencepiece==0.2.2. sentencepiece was already installed. protobuf was only a constraint, not in the pip package list.

Fix on main c37601767f552012f94a1d47f71336178369fa5a:
- protobuf==7.36.1 added to the isolated pip install
- load_qwen35_tokenizer no longer passes fix_mistral_regex
- load_dataprep_tokenizer swallows ImportError only when the missing module name is sft_stop_token_utils
- CPU smoke sft_tokenizer_cpu_smoke.py runs after the merged model download and before GPU smoke; failure prints SETUP_FAILED rc=1
- SMOKE_BEFORE_TRAIN_FAILED is its own log line on setup and smoke logs; monitor sets WeightedFailStop, saves evidence, destroys, and exits 1 instead of throwing adapter-missing

Verify: pytest 50 passed, 1 skipped (no local tokenizer files). Dry READY, DIRTY_OVERRIDES=(none), WATCHDOG_DRY=1. No GPU rented.
