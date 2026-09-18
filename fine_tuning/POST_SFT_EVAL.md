# Post-SFT evaluation

This evaluation isolates generation quality by using the fixed contexts in
`data/qa_test_frozen.jsonl`. It compares the shipped `spurgeon-qa-v2` model
with the pre-SFT `spurgeon-cpt` model using identical raw ChatML prompts and
temperature 0.

## Prerequisites

- Python 3.11–3.13 with `python-dotenv` and `pytest`
- Ollama running locally
- Ollama models `spurgeon-qa-v2` and `spurgeon-cpt`
- For semantic judging, a configured provider key in `.env`

The evaluator reads judge configuration only through `config.py`. Supported
`SFT_EVAL_JUDGE_PROVIDER` values are `groq`, `openrouter`, `cerebras`, and
`gemini`.
Explicit `SFT_EVAL_JUDGE_BASE_URL`, `SFT_EVAL_JUDGE_API_KEY`, and
`SFT_EVAL_JUDGE_MODEL` values override provider defaults.

## Preflight

```powershell
py -3.13 -m pytest tests/test_sft_eval.py tests/test_qa_rewrite_checks.py -q
ollama list
```

Run a small generation-only smoke:

```powershell
py -3.13 fine_tuning/scripts/evaluate.py `
  --candidate ollama:spurgeon-qa-v2 `
  --baseline ollama:spurgeon-cpt `
  --limit 5 `
  --output fine_tuning/eval_results/post_sft_eval_smoke.json
```

An exit code of 1 means one or more release gates failed; the JSON and human
review files are still valid evaluation evidence. Connection, parsing, and
configuration errors raise an exception instead.

## Full paired evaluation

```powershell
$env:SFT_EVAL_JUDGE_PROVIDER = "gemini"
py -3.13 fine_tuning/scripts/evaluate.py `
  --candidate ollama:spurgeon-qa-v2 `
  --baseline ollama:spurgeon-cpt `
  --candidate-artifact fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_gguf/spurgeon-qa-v2.Q4_K_M.gguf `
  --source-adapter-artifact fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_lora_v2/lora/adapter_model.safetensors `
  --judge `
  --judge-orders 2 `
  --output fine_tuning/eval_results/post_sft_eval.json
```

The Gemini default is pinned to `gemini-3.5-flash-lite`; the OpenRouter
fallback is pinned to `nvidia/nemotron-3-super-120b-a12b:free`. Release gating
rejects reports that mix served judge models. The two judge orders swap
candidate and baseline positions. The report does not contain API keys.

If a judge run is interrupted or rate-limited, resume from the deterministic
checkpoint without regenerating model answers:

```powershell
$env:SFT_EVAL_JUDGE_PROVIDER = "gemini"
py -3.13 fine_tuning/scripts/evaluate.py `
  --judge-existing-report fine_tuning/eval_results/post_sft_eval.json `
  --judge-orders 2 `
  --judge-batch-size 5
```

## Outputs and gates

- `post_sft_eval.json`: complete paired generations, hashes, deterministic
  metrics, judge decisions, and aggregate gates
- `post_sft_eval_human_review.md`: every deterministic or semantic failure
  plus a seeded pass sample
- `ollama_smoke.json`: separate three-prompt serving smoke evidence

Release requires all of:

- groundedness at least 4/5
- refusal recall at least 85%
- context echo at most 2%
- corrupt output exactly 0%
- `<|im_end|>`/API stop rate at least 85%
- leaked turns at most 2%

Run serving verification separately:

```powershell
py -3.13 fine_tuning/scripts/smoke_test_ollama.py --model spurgeon-qa-v2
py -3.13 fine_tuning/scripts/verify_sft_stop_tokens.py `
  --phase 5 `
  --ollama-model spurgeon-qa-v2
```

Do not export or switch application defaults when the persisted report fails
any gate.
