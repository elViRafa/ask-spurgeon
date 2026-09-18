---
store_path: fine-tuning/qwen35-sft-special-tokens
title: "Qwen3.5-4B SFT special-token contract"
summary: "**Model:** `unsloth/Qwen3.5-4B-Base` (GATE-0 uses the same tokenizer on the CPT merge)"
priority: high
tags: [sft, qwen35, eos, chatml, tokenizer]
schema_version: 1.3
last_updated: "2026-08-28T22:36:58-04:00"
evidence: [fine_tuning/scripts/audit_qwen35_special_tokens.py, fine_tuning/data/qwen35_special_token_audit.json, fine_tuning/scripts/_gen_sota_sft_notebooks.py, fine_tuning/models/Modelfile.qwen35-spurgeon-qa-v2]
---

# Qwen3.5-4B SFT special-token contract (2026-08-29)

**Model:** `unsloth/Qwen3.5-4B-Base` (GATE-0 uses the same tokenizer on the CPT merge). Not Qwen2.5. **Do not hardcode 151644/151645.**

## Live ids (tokenizer-only audit PASS)

| Token | Id | Role |
|---|---|---|
| `<\|endoftext\|>` | **248044** | Native `eos_token` (CPT / document EOT). Safety generate stop. |
| `<\|im_start\|>` | **248045** | ChatML turn open; Ollama stop |
| `<\|im_end\|>` | **248046** | ChatML **turn stop** (SFT generate + Ollama stop) |
| `<\|vision_pad\|>` | **248055** | Native **pad** on this Base (existing special; not im_end) |

- `vocab_size=248044`, `len(tokenizer)=248077`. Specials live in added_tokens. **Do not assert `len == vocab_size`** — that aborts a stock Qwen3.5 tokenizer. Never-resize = `len` unchanged after pad/template setup.
- Base has **no `chat_template`**. Inject plain ChatML (no Instruct thinking/vision/tool jinja). Demo: system/user/assistant each end with `<\|im_end\|>`.
- Do **not** set `tokenizer.eos_token = im_end` (would risk pad=stop). Generate with `eos_token_id=[im_end_id, eot_id]`.
- Pad: keep native `vision_pad` if present; if pad is None or equals im_end, set pad to `endoftext`.
- Unwrap VL Processor before tokenizing text (`bugs/qwen35-processor-text-as-image`).
- Collator: `DataCollatorForSeq2Seq(label_pad_token_id=-100)` so pad!=im_end still does not clone labels.
- Never `add_special_tokens` / resize / LoRA embed+lm_head unless S5 shows ChatML tokens are not emitted.

## Files
- `fine_tuning/scripts/audit_qwen35_special_tokens.py` + `fine_tuning/data/qwen35_special_token_audit.json`
- D/E/F regenerated from `_gen_sota_sft_notebooks.py`
- `fine_tuning/models/Modelfile.qwen35-spurgeon-qa-v2` — im_end after system/user; `repeat_penalty 1.05`

Special-token contract implemented 2026-08-29: D/E/F regenerated, Modelfile fixed, audit JSON at `fine_tuning/data/qwen35_special_token_audit.json`. Operator next: Track A bulk rewrite (`--apply --limit 50`) then stock-base D→E→F; do not mix with CPT volume `7hb931c5oe`. See `fine-tuning/next-session-handoff`.
