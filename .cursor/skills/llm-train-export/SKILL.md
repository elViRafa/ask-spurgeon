---
name: llm-train-export
description: >-
  Develop and refine Ask Spurgeon CPT/SFT training code, eval gates, merge,
  GGUF, Ollama, and Hub export. Use when writing train/eval/export scripts,
  changing a recipe, promoting an adapter, or when Grok Bot Foundry / a Cloud
  Agent is asked to improve model training.
---

# LLM train + export (code path)

You write and refine the **code and recipes**. You do not rent GPUs. Hand paid
runs to Forge (`/gpu-train-ops`) after the operator says **go**.

Repo: `https://github.com/elViRafa/ask-spurgeon.git`

## Pipeline (do not skip stages)

```text
Qwen3.5-4B-Base
  → CPT LoRA (Vast, isolation C)
  → Hub only if C wins
  → merge 16-bit HF
  → SFT (grounded Q&A, not persona)
  → F §5 gates
  → GGUF + Ollama + app
```

CPT handoff: `pretraining/cpt-next-session-handoff`
SFT export gate script: `fine_tuning/scripts/sft_export_if_gates.ps1`
Ollama smoke: `fine_tuning/scripts/smoke_test_ollama.py`
CPT smoke: `continued_pretrain/scripts/smoke_test_ollama_cpt.py`

## Current board (2026-09-26)

- CPT next: v6 replay from nested `ddbbee3a`, session `vast_cpt_s7_replay`.
  Hub CPT stays Phase A `06354dfc`. No rent until go.
- GATE-0 SFT + Q4 GGUF + `spurgeon-qa-v2` Ollama already shipped once.
  New EXPORT still requires F §5 via `sft_export_if_gates.ps1`.
- Assistant is a **knowledge Q&A speaker**, never Spurgeon-as-character.

## What you may do without go

- Read runbooks, metrics, isolation-C tables, session JSON.
- Open a PR that fixes a trainer, eval, merge, or export script.
- Propose a recipe change (LR, mix, halt) as a written plan + dry command.
- Draft the Cloud Agent prompt Forge should not write.

## What needs go

- Any GPU rent (tell Forge; do not create the instance yourself).
- Hub overwrite (CPT or SFT).
- Running `sft_export_if_gates.ps1` / uploading GGUF.
- Rebuilding QA mix with `build_qa_mix_v2.py` (wipes overlays).
- Changing tokenizer stop contract (Qwen3.5 ids are not 151644/151645).

## Refine loop

1. Name the failure with evidence (log line, CE table, F metric).
2. Change **one** knob. Do not raise LR and redraw holdouts in the same PR.
3. Dry the orchestrator (no `-Go`).
4. Ask operator for go → Forge launches and watches.
5. After fetch: isolation C (CPT) or `sft_export_if_gates.ps1` (SFT).
6. Promote Hub only on a written win. Otherwise keep the current Hub SHA.

## Export gates (SFT)

`sft_export_if_gates.ps1` must see all of:

- refusal_accuracy ≥ 0.85
- echo_rate ≤ 0.02
- corrupt_rate == 0
- im_end_stop_rate ≥ 0.85
- leaked_turn_rate ≤ 0.02
- groundedness ≥ 4.0
- judge_model_consistent
- SHA of candidate artifact, source adapter, and frozen dataset match the report

Tokenizer: `<|im_end|>` is the SFT turn stop. Do not set `eos_token = im_end`.
Do not hardcode 151644/151645.

## Hard do-nots

- Train or llama.cpp-convert on the Grok Bot computer or a Cloud Agent CPU
  unless the operator explicitly asks for a tiny smoke.
- HF-resume `checkpoints_sota` / 2050 / 2400.
- Overwrite `a_output_v3` / `v4` / `v5` or Phase B fetch.
- Log `HF_TOKEN`, Vast/Runpod keys, or `.env`.
- Speak as Spurgeon in prompts or eval gold.
- Git-clone this repo onto a training pod.

## PR / Cloud Agent prompt shape

```text
Repo: elViRafa/ask-spurgeon
Skill: /llm-train-export
Change: <one knob or one script>
Proof: pytest and/or dry orchestrator output
Do not: rent GPU, push Hub, commit .env
```
