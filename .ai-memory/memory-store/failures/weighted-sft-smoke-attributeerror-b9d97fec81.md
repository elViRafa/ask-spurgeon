---
store_path: failures/weighted-sft-smoke-attributeerror-b9d97fec81
title: "weighted SFT smoke AttributeError tokenizers.Tokenizer has no attribute backend_"
summary: "weighted SFT smoke AttributeError tokenizers.Tokenizer has no attribute backend_tokenizer then ImportError protobuf library was not found; broad except ImportError retried fix_mistral_regex"
priority: medium
tags: [failure, fix, protobuf, sft, tokenizer, vast]
schema_version: 1.3
last_updated: "2026-10-16T18:10:38-03:00"
occurrences: 1
error_signature: "weighted sft smoke attributeerror tokenizers.tokenizer has no attribute backend_tokenizer then importerror protobuf library was not found; broad except importerror retried fix_mistral_regex"
failure_key: attributeerror
---

## Occurrence 1 — 2026-10-16T18:10:38-03:00

**Error:**
weighted SFT smoke AttributeError tokenizers.Tokenizer has no attribute backend_tokenizer then ImportError protobuf library was not found; broad except ImportError retried fix_mistral_regex

**Fix:**
Install protobuf==7.36.1 in the venv, stop passing fix_mistral_regex, re-raise ImportError from inside load_qwen35_tokenizer, and run a CPU tokenizer smoke that prints SETUP_FAILED rc=1 before GPU smoke. Main c376017.
