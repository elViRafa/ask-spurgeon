# PLAN — Fable 5 review: improving the Spurgeon Q&A fine-tune (SFT)

**Date:** 2026-07-13
**Scope:** Instruction fine-tuning (SFT) of the Spurgeon Q&A generator, based on
`fine_tuning/notebooks/D_qa_data_prep.ipynb`, `E_qa_training.ipynb`, `F_qa_eval.ipynb` and the
`fine_tuning/data/spurgeon_qa_train_final.jsonl` dataset (2,787 examples).
**Goal:** a chat model that, given the *exact* context the Ask Spurgeon app retrieves at serve
time, answers in Spurgeon's voice, strictly grounded in that context, refuses honestly when the
context is insufficient, and stops cleanly — deployable via GGUF/Ollama or llama.cpp Space.

**Companion plan:** [`../../continued_pretrain/PLAN_FABLE5_TO_IMPROVE_CPT.md`](../../continued_pretrain/PLAN_FABLE5_TO_IMPROVE_CPT.md)

---

## 0. Position in the pipeline — the base model is the CPT v2 output

This SFT phase **chains on the model produced by the CPT plan**. It does not start from a stock
instruct model.

```
Qwen3.5-4B-Base ──CPT v2 (theology mix, B_training_sota)──▶ theology_cpt_v2_merged_hf
                                                              │
                                                              ▼  (this plan)
                                              SFT v2 (grounded Q&A, ChatML) ──▶ spurgeon_qa_v2
                                                              │
                                                              ▼
                                          GGUF q4_k_m / f16 → Ollama / llama.cpp Space → app
```

**Hard dependency (GATE-0):** SFT v2's *final* training run starts only when all of:

1. CPT v2 passed its §5 success gate (see CPT plan) and `C_eval_sota` produced the
   **16-bit merged model** (`save_pretrained_merged`, HF folder with `config.json` +
   safetensors + tokenizer).
2. That folder is published as a Kaggle dataset — contract:
   `/kaggle/input/datasets/rafaelvieira1/theology-cpt-v2/theology_cpt_v2_merged_hf/`
   (mirror of today's `spurgeon-lora-final/spurgeon_phase1_merged_hf` convention).
3. The CPT run config (manifest SHA, base model id, unsloth commit) is copied alongside it, so
   the SFT run config can reference exactly which CPT artifact it trained on.

**Parallel work is allowed and encouraged:** everything in Phases 0–3 except the final run can be
built and debugged **now** against stock `Qwen/Qwen3.5-4B-Base` (same architecture and tokenizer
as the future CPT v2 output). The day CPT v2 lands, only the `BASE_MODEL_NAME` changes.

**Fallback:** if CPT v2 slips or fails its gate, do **not** chain on the old
`spurgeon_phase1_merged_hf` for anything shippable — it is Qwen2.5-3B (Qwen *Research* license,
non-commercial) and per CPT F1 it was trained on truncated data. Use it only to smoke-test
notebook plumbing.

---

## 0.5 TL;DR — the six things that matter most

1. **The pipeline has never actually trained on the Spurgeon data (F1).** `E_qa_training.ipynb`
   is the stock Unsloth Alpaca demo: its recorded run trained on **yahma/alpaca-cleaned
   (51,760 examples) for 60 steps**, and its last recorded state fails to even load the base
   model. Notebook D's prepared datasets are never consumed by E. E must be rewritten, not
   patched.
2. **Three-way template mismatch (F2):** D formats data as Qwen ChatML, E trains with the
   **Alpaca** prompt, F evaluates with **ChatML** again — on a base (completion) model. The
   garbage seen in F's outputs (context regurgitation, `pist` tokens, loops) is exactly what this
   produces. One canonical template, defined once, used by data prep + training + eval + Ollama
   Modelfile.
3. **Train/serve mismatch (F3):** the app sends **6 chunks × 768 tokens** with
   `[Sermon N — "Title", Volume V | Text: ref]` headers under `SYSTEM_PROMPT_NEUTRAL`; training
   examples have **one bare ~330-token chunk** under a different system prompt, at seq 2048 —
   shorter than the app's prompt alone. Align both sides (Phase 1 data shape + app config) or the
   deployed model runs out-of-distribution on every request.
4. **No completion-only masking (F4):** with `train_on_responses_only` absent and answers ~240
   chars median vs ~1,300-char contexts, ≥80% of the loss is on the *prompt* — the model is
   literally being taught to reproduce `CONTEXT:` blocks (F's outputs show it doing so).
5. **Data is the moat, again (F5):** 2,787 single-chunk examples, ~1% refusals, no citation
   behavior, no multi-chunk examples. Target ~5–6k examples shaped exactly like serving traffic,
   with a 10–15% insufficient-context slice and a catechism Q/A slice (ready-made from the CPT
   corpus, as the CPT plan §Phase 4 anticipated).
6. **Never resize the vocab; gate the export (F6/F7).** F's run shows an added `<|PAD_TOKEN|>`
   (id 151665 — beyond the stock vocab) — the known GGUF vocab-shift corruption
   (`bugs/ollama-tokenizer-corruption-fix`). And F exported + uploaded the GGUF *after* producing
   visibly broken generations. Pad with an existing token, and make merge/GGUF/upload conditional
   on the §5 eval gate.

---

## 1. Current state (what actually exists)

### 1.1 Notebooks

| Notebook | Intent | Actual state |
|---|---|---|
| `D_qa_data_prep.ipynb` | JSONL → ChatML → 95/5 split → `save_to_disk` | Works, but its output (`qa_dataset_train/val`) is **never loaded by E**; applies `qwen-2.5` template with `unsloth/Qwen2.5-3B-Instruct` tokenizer; sets `eos = <|im_end|>` |
| `E_qa_training.ipynb` | SFT on the phase-1 CPT model | Stock Unsloth Alpaca demo, lightly edited. Loads raw JSONL (bypasses D), formats with **Alpaca prompt**, `max_steps=60`, r=16/α=16, no eval set, no masking, no run config. Recorded run: base-model load **failed** (`No config file found`), and the training log shows **51,760 examples** (alpaca-cleaned), i.e. the persisted run never saw Spurgeon data |
| `F_qa_eval.ipynb` | Qualitative battery + GGUF export + HF upload | References undefined `messages_template` and `text_streamer` (only ran on stale kernel state); sampled generation (T=0.3) not reproducible; outputs show context echo, repetition loops, corrupted `pist` tokens; EOS at inference = `<|endoftext|>` (not `<|im_end|>`); **exports GGUF and uploads to HF unconditionally** |
| `merge_cells.json`, `new_gguf_cells.json` | cell payloads to splice in | Reference `meta-llama/Llama-3.1-8B-Instruct` — from the abandoned May plan; stale |

### 1.2 Data — `spurgeon_qa_train_final.jsonl` (audited 2026-07-13)

- 2,787 records, single schema `{"messages": [system, user, assistant]}` — good.
- One system prompt: *"You are Charles Haddon Spurgeon. Answer using only the information in the
  provided CONTEXT. Stay very close to the actual text."*
- User = `CONTEXT:\n{chunk}\n\nQUESTION:\n{q}` with chunk ≈ 1,313 chars p50 (max 1,424 —
  generator chunked at 1,200 chars / 400 overlap) ⇒ **~330 tokens of context per example**.
- Assistant: 238 chars p50 / 401 p90 / 3,356 max — short answers.
- Refusal-ish answers ("the context does not contain…"): **31 (1.1%)**.
- 400-char chunk overlap in the generator ⇒ adjacent examples share up to a third of their
  context text — near-duplicate risk, never deduped.

### 1.3 Serving side (what the model will actually see — from `app.py`, `config.py`, `utils/prompts.py`)

- Retrieval: `similarity_top_k=6`, `CHUNK_SIZE=768` (tokens), `CHUNK_OVERLAP=128` ⇒ context ≈
  **4,600 tokens**, each block headed `[Sermon {n} — "{title}", Volume {v} | Text: {ref}]`.
- System prompt: `SYSTEM_PROMPT_NEUTRAL` — a modern-assistant prompt, **not** the training
  persona prompt; plus `USER_PROMPT_TEMPLATE` wrapping.
- Chat history: last 6 messages may be prepended (`build_chat_messages`) — multi-turn exists at
  serve time, zero multi-turn examples in training data.

### 1.4 What already exists and is worth keeping

- Generator scripts (`generate_qa_pairs_openrouter.py` / `_ollama.py`) with a good
  fidelity-first teacher prompt — need upgrades, not replacement.
- `tests/evaluate_rag.py` + `tests/compare_prompts.py` — an LLM-as-judge harness over the real
  index; reuse it for Phase 3 instead of building a new one.
- The fidelity-first contract from `FINE_TUNING_PLAN.md` (2026-05-31) — still the right
  philosophy; that plan's Llama-3.1-8B stack is superseded by the CPT chain.

---

## 2. Findings (ordered by impact)

### F1 — CRITICAL: E never trained on the project's data; D→E→F is not actually a pipeline

Evidence in §1.1. Consequences: every downstream artifact (the `lora_model` Kaggle dataset F
warns about, the uploaded `qwen2.5-3b-spurgeon-qa-gguf` GGUF) is of unknown provenance — F's own
markdown warns the adapter input may contain "stale weights… corrupted output (vinfos/spep
tokens)". **Treat all existing SFT artifacts as invalid.** Rewrite E from a clean Unsloth ChatML
SFT skeleton; make it load D's `save_to_disk` output (or take over D's role entirely — see G3).

### F2 — CRITICAL: one template must rule data prep, training, eval, and deployment

Current state: D = ChatML (`qwen-2.5`), E = Alpaca, F = ChatML; training EOS `<|im_end|>` vs
inference EOS `<|endoftext|>`; F's pad token id 151665 is an **added** token (vocab resize) —
the documented cause of the Ollama/GGUF corruption in project memory.

**Decision (T1):** canonical template = the ChatML template shipped by the **CPT v2 base's own
tokenizer** (Qwen3.5 family). Rules:

- One `SPURGEON_CHAT_TEMPLATE` decision recorded in a config cell, identical in D/E/F sota
  notebooks and the Ollama Modelfile.
- `eos_token = <|im_end|>` for SFT; generation stops on `<|im_end|>`.
- **Never call `add_special_tokens` / never resize embeddings.** Pad with an existing token
  (`<|endoftext|>` or a reserved `<|fim_pad|>`-class token — verify id exists in the stock
  vocab). Rationale: `bugs/ollama-tokenizer-corruption-fix`.
- Verify ids at runtime, don't hardcode Qwen2.5 ids (Qwen3.5 may differ):

```python
# S2 — template & special-token audit (run in E_sota after tokenizer load)
for t in ["<|im_start|>", "<|im_end|>", "<|endoftext|>"]:
    ids = tokenizer(t, add_special_tokens=False)["input_ids"]
    print(t, "->", ids, "(single id)" if len(ids) == 1 else "(NOT ATOMIC — fix)")
print("vocab_size:", tokenizer.vocab_size, "len:", len(tokenizer))  # must be equal pre/post
print("eos:", repr(tokenizer.eos_token), tokenizer.eos_token_id)
print("pad:", repr(tokenizer.pad_token), tokenizer.pad_token_id)    # must be an EXISTING id
demo = tokenizer.apply_chat_template(
    [{"role":"system","content":"S"},{"role":"user","content":"U"},
     {"role":"assistant","content":"A"}], tokenize=False)
print(demo)  # eyeball: one im_start/im_end pair per turn, assistant ends with <|im_end|>
```

One extra check because the base is a **CPT'd base model**: `<|im_start|>`/`<|im_end|>` rows in
`embed_tokens` were touched neither by base-model pretraining emphasis nor by the CPT run
(theology corpus contains no ChatML). This is normally fine (Qwen bases SFT well on ChatML), but
verify it's learning, not fighting: if template-compliance failures persist after ~100 steps
(S5 probe), consider adding `embed_tokens`+`lm_head` to LoRA targets as a fallback — not the
default.

### F3 — CRITICAL: training data must be shaped like serving traffic (and seq length sized to it)

The app's prompt alone (~4.8k tokens with 6×768-token chunks + system + question) exceeds the
notebooks' `max_seq_length=2048`. Two-sided alignment, both cheap:

1. **Data side (Phase 1):** build examples from the *real retriever* output — k chunks with the
   real `[Sermon …]` headers via `format_context()`, the canonical system prompt, questions from
   the question bank. Sample k ∈ {1..5} (weighted toward 3–4) so the model sees both single- and
   multi-chunk contexts.
2. **App side (one-line config):** when `LLM_PROVIDER=openai` (fine-tuned path), set
   `similarity_top_k=4`. 6×768 was tuned for Groq-70B's context appetite; 4 blocks ≈ 3.1k tokens
   keeps the whole exchange inside **seq 4096** for the 4B on a T4.
3. **Canonical system prompt (T2):** pick ONE — recommendation: keep the training persona prompt
   ("You are Charles Haddon Spurgeon…"), extend it with the refusal instruction and citation
   rule, define it as a constant in `config.py`, and have data-gen, training, eval, the app path
   for the fine-tuned model, and the Ollama Modelfile all import/copy that exact string.
   `SYSTEM_PROMPT_NEUTRAL` remains for the Groq path only.

Diagnostic to size the final choice:

```python
# S1 — token-length audit of the built dataset (run in D_sota before saving)
import numpy as np
lens = [len(tokenizer(x["text"])["input_ids"]) for x in ds]
print("p50/p90/p99/max:", np.percentile(lens, [50, 90, 99]).astype(int), max(lens))
over = sum(l > MAX_SEQ_LENGTH for l in lens)
print(f"examples over {MAX_SEQ_LENGTH}: {over} ({over/len(lens):.1%})  # must be ~0")
```

### F4 — CRITICAL: train on completions only

Use Unsloth's masking so loss falls only on assistant spans:

```python
from unsloth.chat_templates import train_on_responses_only
trainer = train_on_responses_only(
    trainer,
    instruction_part="<|im_start|>user\n",
    response_part="<|im_start|>assistant\n",
)
```

And **prove** it before training:

```python
# S3 — masking audit: decode only the supervised tokens of row 0
row = trainer.train_dataset[0]
kept = [t for t, l in zip(row["input_ids"], row["labels"]) if l != -100]
print(tokenizer.decode(kept))   # must be ONLY the assistant answer + <|im_end|>
frac = len(kept) / len(row["input_ids"])
print(f"supervised fraction: {frac:.1%}")  # expect ~10-25% for grounded QA
```

Side effect worth knowing: supervised tokens/epoch ≈ Σ(answer tokens) ≈ only ~0.2M on the current
2,787 short answers. That is *tiny* — more examples and 2–3 epochs matter more than any LR tweak.

### F5 — Data v2 composition (the highest-ROI work)

Current data is one-note: single short chunk → short paraphrase answer, 1% refusals, no
citations, no off-topic handling, no multi-turn. Target mix in Phase 1 (~5,500–6,500 examples):

| Slice | Share | Source / notes |
|---|---|---|
| Grounded Q&A, multi-chunk serve-shaped | ~60% | regenerate via teacher over **retriever output** (k=1–5, real headers); answers must cite `[Sermon n]` when quoting |
| Grounded Q&A, existing 2,787 reformatted | ~15% | keep the good ones: rewrap user msg into the serve-shaped format, dedupe overlap (1d below), judge-filter |
| Insufficient context → honest refusal | ~12% | pair real questions with deliberately *mismatched* retrieved chunks; answer = persona-voiced "the provided sermons do not address…" |
| Catechism/confession Q&A | ~8% | WSC / 1689 from the CPT corpus as CONTEXT, question = the catechism question — ready-made seed data per CPT plan §Phase 4 |
| Off-topic / out-of-persona redirects | ~3% | modern/secular questions → brief in-persona redirect to what the sermons do address; **no generic-assistant (Alpaca-style) replay — it dilutes the persona** |
| Multi-turn (2-turn) grounded follow-ups | ~2–5% | optional; matches `build_chat_messages` history behavior |

Quality gates (mirror CPT Phase 1):

- **1d-dedup:** hash normalized answer texts + context head/tails; the 400-char generator overlap
  means near-dupes exist today. Report top-20 most-frequent answer prefixes in the manifest.
- **Faithfulness filter:** every teacher-generated pair judged (reuse `tests/evaluate_rag.py`
  judge with a fixed rubric); drop pairs scoring <4/5 on grounding. Log the drop rate.
- **Manifest + guard (G2 equivalent):** the builder writes `qa_mix_manifest.json` (slice counts,
  shares, SHA256, generator model, judge model, drop stats) and **fails loudly** if any slice is
  empty — no silent single-slice datasets.
- **Frozen splits:** 95/5 train/val plus a **frozen 100-question test set** (never trained on,
  half answerable / half insufficient-context) saved separately for Phase 3 and all future runs.

### F6 — Export/deploy correctness

1. **Gate the merge/GGUF/HF-upload on the §5 eval gate.** F currently exports and uploads
   unconditionally — a corrupted model went to the Hub. Split F_sota: eval cells first,
   export cells behind an explicit `EXPORT = eval_passed` flag.
2. **Naming:** the last upload pushed `spurgeon_phase1_merged_hf.F16.gguf` into a repo named
   `qwen2.5-3b-spurgeon-qa-gguf`. v2 contract: HF repo `rafaelvieirar1r/qwen3.5-4b-spurgeon-qa`,
   files `spurgeon-qa-v2.F16.gguf` / `spurgeon-qa-v2.Q4_K_M.gguf`; Ollama model `spurgeon-qa-v2`.
3. **Modelfile must encode the training contract:** ChatML template, the canonical system prompt
   as default `SYSTEM`, `PARAMETER stop "<|im_end|>"`, temperature ≤0.4 (fidelity-first).
4. Reuse the documented GGUF vocab-shift fix if the exported tokenizer drifts
   (`bugs/ollama-tokenizer-corruption-fix`); F2's no-resize rule should prevent it entirely.

### F7 — Evaluation is not decision-grade

F's battery is 6 sampled generations eyeballed by a human, with two `NameError`s that prove the
notebook can't run top-to-bottom. Phase 3 replaces it with numbers (deterministic battery,
LLM-judge faithfulness/style, refusal accuracy, structural-echo rate, baseline comparisons).

### F8 — Reproducibility & hygiene

1. Unpinned `unsloth @ git+…HEAD` in all three notebooks — pin to the same commit CPT G1 pins.
2. `os.environ["CUDA_VISIBLE_DEVICES"]="0"` is set **after** `import unsloth` in E (banner shows
   `Num GPUs = 2`) — set it in the first cell, before any CUDA import.
3. No run config: save `sft_run_config.json` (dataset SHA + manifest hash, base-model path +
   CPT run config hash, LoRA/TrainingArguments, unsloth commit, `pip freeze` path, S1–S5
   results) next to the adapter, mirroring CPT F6.
4. The "patched_adapter" `copytree` hack in F exists because adapter configs bake absolute base
   paths. Keep the patch (it's pragmatic) but make it a small function with a printed
   before/after, and always pair adapter datasets with the base they were trained on in the
   run config.
5. Delete or archive `merge_cells.json` / `new_gguf_cells.json` (Llama-era leftovers) and the
   dead commented Alpaca blocks. One source of truth per notebook (CPT G3 applies here too).

---

## 3. The plan

### Phase 0 — Decisions, diagnostics & scaffolding (½–1 day, no GPU needed except S-cell smoke test)

| ID | Task | Acceptance |
|---|---|---|
| T1 | Canonical template decision (F2): ChatML from CPT-v2 tokenizer; eos `<|im_end|>`; pad = existing token; no resize | Recorded in a config cell shared by D/E/F_sota |
| T2 | Canonical system prompt (F3.3) as a constant in `config.py`, imported everywhere | One string, five consumers (datagen/train/eval/app/Modelfile) |
| T3 | App alignment decision: `similarity_top_k=4` + `MAX_SEQ_LENGTH=4096` for the fine-tuned path | Config diff prepared (not merged until §5 passes) |
| S2 | Template/special-token audit cell (F2) on stock Qwen3.5-4B-Base | All tokens atomic, vocab length unchanged |
| G1 | Pin unsloth commit (same as CPT), save `pip freeze` | Same env across D/E/F sessions |
| G3 | Create `D_qa_data_prep_sota.ipynb` / `E_qa_training_sota.ipynb` / `F_qa_eval_sota.ipynb` (originals frozen as phase-2 baseline); archive stale `*_cells.json` | Clean notebooks run top-to-bottom on stock base |
| GATE-0 | Confirm CPT v2 artifact contract (§0) with the CPT runbook | Path + contents agreed before the final run |

### Phase 1 — Data v2 (1–2 days; the highest-ROI phase)

1. **Builder script** `fine_tuning/scripts/build_qa_mix.py` (single entry point, mirrors
   `07_build_theology_mix.py`): takes the question bank + retriever index + teacher model,
   emits `qa_mix_train.jsonl` / `qa_mix_val.jsonl` / `qa_test_frozen.jsonl` +
   `qa_mix_manifest.json`. Slices and shares per F5 table; `--allow-partial` escape hatch only.
2. **Serve-shaped contexts:** retrieve with the app's own `format_context()` so headers match
   byte-for-byte; sample k∈{1..5}; questions from `tests/rag_test_questions.py` +
   `data/spurgeon_questions.txt` + teacher-generated new ones (detail-oriented rule kept).
3. **Refusal slice:** mismatched retrievals (retrieve for question A, ask question B from a
   different doctrinal area) + genuinely unanswerable questions; answers in persona, no apology
   spiral, ≤3 sentences, may point to what the context *does* cover.
4. **Citation behavior:** teacher instructed to cite `[Sermon n]` inline when quoting or closely
   paraphrasing a specific block; at least half the multi-chunk examples must contain ≥1 citation.
5. **Judge filter + dedup + manifest** per F5. Drop-rate and top-duplicate report reviewed by hand.
6. **S1 token audit** on the built set; adjust k-weights until >4096-token examples ≈ 0%.

Acceptance: manifest shows all slices non-empty within ±3 pts of target shares; frozen test set
saved; S1 clean; spot-read 20 random examples (style + grounding pass by eye).

### Phase 2 — Training v2 (`E_qa_training_sota.ipynb`)

Configuration (deltas vs current E in **bold**):

| Setting | Value | Why |
|---|---|---|
| Base model | **CPT v2 merged (GATE-0); stock Qwen3.5-4B-Base for dev runs** | §0 |
| Load | 4-bit QLoRA, `max_seq_length=`**4096** | F3; T4 16 GB fits 4B @ 4096 with unsloth GC |
| LoRA | **r=32, α=32**, dropout 0, attn+MLP only (no embed/lm_head by default — F2 fallback only) | SFT on ~6k examples doesn't need CPT-scale rank |
| Template | **ChatML per T1**, dataset from **D_sota's `save_to_disk` output** (E must not re-format) | F1/F2 |
| Masking | **`train_on_responses_only` + S3 audit** | F4 |
| Packing | **False** (short conversations, masking simpler unpacked) | |
| Batch | 2 × accum 8 (fallback 1 × 16 if OOM at 4096) | ~16 seq/step |
| LR | **1e-4 cosine, `warmup_ratio 0.03`**, adamw_8bit, wd 0.01, fp16, seed 3407, grad clip 1.0 | gentler than 2e-4 to preserve CPT voice under a persona already close to target |
| Epochs | **2, `num_train_epochs` (kill the `max_steps=60` demo)**; 3rd epoch only if val still falling | F4 note: supervised tokens are scarce |
| Eval | **`eval_dataset=val split`, `eval_steps` ~10×/epoch, `load_best_model_at_end=True`** | first time val is wired at all |
| Logging | **run config JSON (F8.3)**, wandb optional | traceability |
| S5 probe | **every ~100 steps: 2 fixed greedy generations** (1 answerable, 1 refusal) printed | catch template non-compliance / context echo early, mid-run |

Budget: ~6k examples × ~2 epochs ÷ 16 seq/step ≈ **750 steps**; at seq 4096 on a single T4
expect roughly 2–5 h — one Kaggle session, no resume machinery needed (keep `save_steps` anyway).

VRAM fallback ladder: batch 1×16 → seq 3072 + re-shape data k≤3 → r=16. (Embedding training is
not on the ladder; it's an F2 fallback with its own justification.)

### Phase 3 — Evaluation v2 (`F_qa_eval_sota.ipynb`) — numbers, then vibes

All generation **greedy (`do_sample=False`), fixed seed**, `max_new_tokens=400`, stop on
`<|im_end|>`. Sampled generations allowed at the end, for flavor only.

1. **Frozen battery:** the 100-question frozen test set (50 answerable / 50 insufficient) run
   through the exact serve-shaped prompt. Metrics:
   - **Faithfulness** (LLM-judge, 0–5, fixed rubric + pinned judge model — reuse
     `tests/evaluate_rag.py` harness): mean over answerable set.
   - **Refusal accuracy:** % of insufficient-context items correctly refused; **false-refusal
     rate** on answerable items.
   - **Structural echo rate:** % of outputs containing `CONTEXT:` / `QUESTION:` / raw
     `[Sermon` header regurgitation outside a citation — must be ~0 (this is F's failure mode).
   - **Format compliance:** % ending with `<|im_end|>` within budget (no runaway generation).
   - **Citation rate** on multi-chunk answerable items.
   - **Style** (LLM-judge 0–5 rubric: 19th-c. register, direct address, biblical imagery).
2. **Baselines in the same table:** (a) CPT v2 base, zero-shot with the same prompt (what SFT
   adds), (b) the production Groq `llama-3.3-70b` path (what we must beat or match on
   faithfulness, and beat clearly on style).
3. **Blind A/B (human, gold standard):** 30–50 items, v2 vs Groq path, judged on
   faithfulness/voice/overall — this is the ship/no-ship tiebreaker.
4. Only after §5 passes → export cells (merge 16-bit → GGUF f16 + q4_k_m → HF upload → Ollama
   Modelfile smoke test with 3 battery items via `ollama run`).

### Phase 4 — Deploy & app integration

1. Apply T3 config diff: `LLM_PROVIDER=openai` path uses `similarity_top_k=4`, canonical system
   prompt, `CUSTOM_LLM_MODEL=spurgeon-qa-v2`.
2. llama.cpp CPU Space (`spaces/cpu-llama-cpp`) or Ollama-local; verify the Space's prompt
   assembly uses the same template (it must not re-wrap in its own template).
3. Shadow A/B in the app (route N% of queries or a dev flag) before flipping the default.
4. Update `fine_tuning/README.md` — it still documents the Llama-3.1/Colab/1500-example era.

### Phase 5 — Stretch (one variable at a time, after v2 ships)

| ID | Experiment | Hypothesis |
|---|---|---|
| X1 | DPO/ORPO on faithfulness preferences (chosen = judge≥4, rejected = judge≤2 from the same prompt — the Phase-1 filter's rejects are free training signal) | pushes grounding beyond what SFT filtering achieves |
| X2 | Multi-turn slice → full conversational eval | matches app history behavior |
| X3 | Distill the production 70B's best answers (judge-picked) into the 4B as extra SFT data | closes any residual quality gap cheaply |
| X4 | PT-BR answer slice (questions PT, context EN) | Ask Spurgeon's Brazilian users; CPT F7 noted the option |

---

## 4. Target v2 configuration (summary)

```
Base:      theology_cpt_v2_merged_hf (Qwen3.5-4B-Base + CPT v2, 16-bit merged; GATE-0)
           dev runs: Qwen/Qwen3.5-4B-Base
Load:      4-bit QLoRA, seq 4096, fp16 (T4), CUDA_VISIBLE_DEVICES set before imports
Template:  ChatML (tokenizer-native), eos <|im_end|>, pad = existing token, NO vocab resize
Data:      qa_mix v2 ≈ 5.5–6.5k: 60% serve-shaped grounded QA (k=1–5, real [Sermon] headers,
           citations) / 15% legacy reformatted / 12% refusals / 8% catechism / 3% redirects /
           2–5% multi-turn; judge-filtered, deduped, manifest + frozen 100-q test set
LoRA:      r=32, α=32, dropout 0, attn+MLP
Trainer:   SFTTrainer + train_on_responses_only, lr 1e-4 cosine, warmup_ratio 0.03,
           adamw_8bit, wd 0.01, seed 3407, batch 2×8 (→1×16), 2 epochs,
           eval per ~1/10 epoch, load_best_model_at_end, run-config JSON
Eval:      greedy frozen battery + LLM-judge (faithfulness/style) + refusal/echo/format metrics,
           baselines = CPT base zero-shot & Groq-70B path, blind human A/B
Export:    gated: merged 16-bit → GGUF f16 + Q4_K_M → rafaelvieirar1r/qwen3.5-4b-spurgeon-qa →
           Ollama Modelfile (ChatML + canonical SYSTEM + stop <|im_end|>)
```

## 5. Success criteria (quantified) & kill criteria

**Ship v2 when all of:**

1. Pipeline integrity: D→E→F sota run top-to-bottom in one session on the GATE-0 base; S1–S3+S5
   all clean; run config saved.
2. Faithfulness (judge, answerable set): **≥ 4.0/5 mean**, and ≥ Groq-70B path − 0.2.
3. Refusal accuracy ≥ **85%**; false-refusal rate ≤ **10%**.
4. Structural echo rate ≤ **2%**; format compliance ≥ **98%** (clean `<|im_end|>` stop).
5. Style: judge ≥ 4.0/5 mean **and** blind A/B preference vs Groq path ≥ **60%** on voice.
6. GGUF/Ollama smoke test reproduces battery answers (no vocab-shift symptoms: no `pist`-class
   tokens, identical refusal behavior at temperature 0).

**Kill/adjust triggers:**

- S3 shows supervised fraction >50% → masking broken; stop, fix before spending GPU hours.
- Val loss flat from step ~0 → template or masking bug, not a data problem; check S2/S3 first.
- Faithfulness < 3.0 after epoch 1 → data problem: tighten judge filter / raise refusal share;
  don't chase it with LR.
- Persona bleeds ("As an AI…") → hunt contaminated teacher outputs in the mix; the redirect
  slice must be persona-voiced.
- Template non-compliance persists after ~100 steps (S5) → F2 fallback: add embed_tokens+lm_head
  (dual-LR per CPT recipe) and rerun.

## 6. Risk register

| Risk | Mitigation |
|---|---|
| CPT v2 slips → SFT blocked | §0 parallel-path: build/debug everything on stock Qwen3.5-4B-Base; only the final run waits |
| CPT v2 changes voice enough that old QA answers (teacher-written) clash in register | 15% legacy slice is judge-refiltered; X3 can regenerate answers with the CPT model itself as style reference |
| Vocab resize → GGUF corruption (seen: `pist`, `<|PAD_TOKEN|>` 151665) | F2 no-resize rule + S2 audit + memory `bugs/ollama-tokenizer-corruption-fix`; smoke-test GGUF before upload |
| Model regurgitates context (seen in F outputs) | F4 masking + echo metric + refusal slice; echo rate is a ship gate |
| Judge-filter circularity (teacher and judge agree on wrong answers) | different judge model than teacher; 20-example human spot-check per 1k generated |
| Multi-chunk contexts blow seq 4096 | S1 audit + k-weight tuning + app top_k=4 (T3); ladder to 3072/k≤3 |
| Kaggle input dataset staleness (F's warning about `lora_model`) | version Kaggle datasets (`…-v2`, `…-v3`), never overwrite in place; run config records exact dataset slug |
| ChatML-token embeddings undertrained on a base+CPT model | S5 early probe + F2 fallback (embed/lm_head LoRA); known-good precedent: Qwen bases SFT on ChatML routinely |
| T4 OOM at seq 4096 | fallback ladder (§Phase 2); 4B 4-bit + unsloth GC has headroom on 16 GB |
| Space/Ollama re-wraps prompt in its own template (double-templating) | Phase 4.2 explicit check: send raw battery item, compare tokens; Modelfile owns the template |

## 7. Execution checklist (in order)

- [ ] **P0:** T1 template decision + T2 canonical system prompt in `config.py` + T3 app diff drafted
- [ ] **P0:** S2 audit green on stock Qwen3.5-4B-Base; G1 pin; G3 sota notebooks scaffolded, stale JSON cells archived
- [ ] **P1:** `build_qa_mix.py` + question bank expansion → manifest with all slices
- [ ] **P1:** judge filter + dedup pass → drop-rate report reviewed
- [ ] **P1:** S1 token audit clean; frozen 100-q test set saved
- [ ] **P2 (dev):** full D→E dry run on stock base, S3 masking audit green, S5 probes sane
- [ ] **GATE-0:** CPT v2 §5 passed; `theology-cpt-v2` Kaggle dataset live
- [ ] **P2 (final):** train on CPT v2 base, 2 epochs, best-checkpoint selected
- [ ] **P3:** F_sota battery + judge + baselines → §5 scorecard
- [ ] **P3:** blind A/B vs Groq path
- [ ] **P4:** gated export (GGUF f16 + Q4_K_M) → HF → Ollama smoke test → app T3 config + shadow A/B
- [ ] **P4:** update `fine_tuning/README.md`; archive legacy D/E/F + old artifacts as `phase2-legacy`
- [ ] **P5:** stretch experiments (X1 DPO on filter rejects first — the data already exists)

## 8. References

- Unsloth chat templates & `train_on_responses_only`:
  https://docs.unsloth.ai/basics/chat-templates
- TRL SFTTrainer (completion-only loss, packing):
  https://huggingface.co/docs/trl/sft_trainer
- Qwen3.5 model cards / tokenizer & ChatML tokens (verify ids at runtime, not from docs):
  https://huggingface.co/Qwen/Qwen3.5-4B
- Companion plan & artifact contract: `continued_pretrain/PLAN_FABLE5_TO_IMPROVE_CPT.md` (§4.2,
  §5, Phase 4 "Beyond CPT"), `continued_pretrain/KAGGLE_RUNBOOK_V2.md`
- Existing judge harness to reuse: `tests/evaluate_rag.py`, `tests/compare_prompts.py`
- Serving contract source of truth: `config.py` (`CHUNK_SIZE=768`, prompts), `utils/prompts.py`
  (`format_context`, `build_chat_messages`), `app.py` (`similarity_top_k=6` today)
- Project memory: `bugs/ollama-tokenizer-corruption-fix` (GGUF vocab shift),
  `pretraining/cpt-sota-assessment-2026-07`, `bugs/sftconfig-pickle`
