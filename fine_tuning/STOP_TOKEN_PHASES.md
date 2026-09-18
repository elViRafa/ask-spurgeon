# SFT end-of-answer token — phased verification

Turn stop for Qwen3.5 SFT v2 is **`<|im_end|>` (248046)**, not `<|endoftext|>`.
Document EOT (248044) is a safety stop only. Batch pad is **`<|vision_pad|>` (248055)**.

Contract memory: `fine-tuning/qwen35-sft-special-tokens`

## Phase 0 — Tokenizer (local, pre-GPU)

**When:** before any RunPod/Kaggle session.

```powershell
python fine_tuning/scripts/verify_sft_stop_tokens.py --phase 0
python fine_tuning/scripts/audit_qwen35_special_tokens.py
```

**Pass:** ChatML tokens atomic; pad ≠ im_end; demo template includes im_end.

**Fail action:** fix `_gen_sota_sft_notebooks.py` / `sft_stop_token_utils.py`; do not train.

---

## Phase 1 — Training template (local, pre-GPU)

**When:** after qa_mix rebuild, before sync to pod.

```powershell
python fine_tuning/scripts/verify_sft_stop_tokens.py --phase 1
python fine_tuning/scripts/13_sft_local_readiness.py --gate0
```

**Pass:** first train row → ChatML text ends assistant turn with im_end.

**On pod (automatic):** `train_sft_sota.py` S3 assert — im_end in supervised labels; abort if fail.

---

## Phase 2 — CPT merged base probe (GPU, after merge)

**When:** immediately after `/workspace/theology_cpt_v2_merged_hf` is written; **before** SFT train.

```bash
# on pod
python3 -u /workspace/verify_sft_stop_tokens.py --phase 2 --base /workspace/theology_cpt_v2_merged_hf
```

Or locally wired in `sft_remote_merge.sh` after merge.

**Pass:** greedy probes stop with im_end ≥85%, corrupt=0, no leaked turns.

**Fail action:** do **not** start SFT; investigate CPT embed_tokens damage. Fallback: F2 embed/lm_head LoRA on stock base or re-merge from clean Hub v2.

---

## Phase 3 — Post-SFT eval (GPU → local)

**When:** after `eval_sft_sota.py` (EXPORT=False).

```powershell
python fine_tuning/scripts/verify_sft_stop_tokens.py --phase 3 --metrics fine_tuning/kaggle/runpod_sft_gate0/sft_eval_metrics.json
```

**Pass:** `im_end_stop_rate ≥ 0.85`, `corrupt_rate = 0`, `leaked_turn_rate ≤ 0.02`.

**Fail action:** check S3 log from train; do not EXPORT. Fix masking/template before second train.

---

## Phase 4 — Export tokenizer (pre-GGUF)

**When:** after `SFT_EXPORT=1` merge on pod, before GGUF convert.

```powershell
python fine_tuning/scripts/verify_sft_stop_tokens.py --phase 4 --merged path/to/spurgeon_qa_v2_merged_hf
```

**Pass:** exported folder tokenizer still has atomic im_end (248046).

**Fail action:** do not convert GGUF; reload tokenizer **from merged folder** (see `bugs/ollama-tokenizer-corruption-fix`).

---

## Phase 5 — Ollama serve (post-GGUF)

**When:** after `ollama create spurgeon-qa-v2 -f Modelfile.qwen35-spurgeon-qa-v2`.

```powershell
python fine_tuning/scripts/smoke_test_ollama.py --model spurgeon-qa-v2
python fine_tuning/scripts/verify_sft_stop_tokens.py --phase 5 --ollama-model spurgeon-qa-v2
```

**Pass:** no corrupt tokens; im_end stop ≥85% at temp 0.

**Modelfile stops:** im_end, im_start, **and** endoftext (fallback if model emits 248044).

---

## Gate summary

| Phase | Blocks |
|-------|--------|
| 0–1 | any GPU work |
| 2 | SFT train on CPT merge |
| 3 | EXPORT / GGUF |
| 4 | GGUF convert |
| 5 | app `.env` flip to custom model |

Reports: `fine_tuning/data/stop_token_phase{N}.json`
