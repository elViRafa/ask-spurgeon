# M1 — Base-model verification gate (2026-07-13)

## Checks

| Check | Result |
|-------|--------|
| `Qwen/Qwen3.5-4B-Base` exists on HF | **PASS** |
| `unsloth/Qwen3.5-4B-Base` exists | **PASS** |
| `tie_word_embeddings` | **`true`** (root + `text_config`) |
| Unsloth 4-bit / GGUF path | **PASS** — `unsloth/Qwen3.5-4B-GGUF` published; full bnb-4bit name to confirm on Kaggle load |
| D4 after `get_peft_model` | **PENDING** (requires Kaggle GPU / Unsloth runtime) |

## Config facts (from HF `config.json`)

- `model_type`: `qwen3_5`
- `architectures`: `Qwen3_5ForConditionalGeneration`
- `hidden_size`: 2560 · `num_hidden_layers`: 32 · `vocab_size`: 248320
- Hybrid stack: mix of `linear_attention` and `full_attention` layers
- Includes `vision_config` (multimodal family architecture even on “Base”)
- **Tied embeddings** → dual-LR recipe should default to **`embed_tokens` only** (`TRAIN_LM_HEAD = False`) unless D4 shows clean separate head training

## Decision

| Choice | Status |
|--------|--------|
| Flagship model id | `unsloth/Qwen3.5-4B-Base` (or `Qwen/Qwen3.5-4B-Base` if Unsloth wrapper fails) |
| Default LoRA head | **`TRAIN_LM_HEAD = False`** (tied embeddings) |
| Fallback if Unsloth cannot train hybrid qwen3_5 on T4 | **`unsloth/Mistral-7B-v0.3`** (untied, Apache-friendly) — do **not** fall back to Qwen2.5-3B (Research license + known GGUF corruption) |

## Risk (high)

Qwen3.5-4B is **not** a plain Qwen2.5-style dense decoder. CPT on Kaggle must prove:

1. `FastLanguageModel.from_pretrained` loads without error  
2. Packing + SFT/UnslothTrainer run ≥20 steps  
3. Peak VRAM &lt; ~15 GB at seq 2048 / batch 2  

If any fail → fall back per table above; do not multi-session a broken stack.

## Still open (Kaggle only)

- [ ] D4 trainable `embed_tokens` / `lm_head` names + `same_storage`  
- [ ] Pin Unsloth git commit after first good session (G1)  
- [ ] Confirm preferred Unsloth quant id (`…-bnb-4bit` vs base + load_in_4bit)  
