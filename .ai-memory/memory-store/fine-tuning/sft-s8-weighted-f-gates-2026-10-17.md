---
store_path: fine-tuning/sft-s8-weighted-f-gates-2026-10-17
title: "Weighted S8 SFT F gates FAIL on refusal"
summary: "**FAIL** — do **not** promote Hub/Ollama `spurgeon-qa-v2`"
priority: high
tags: [sft, f-gates, refusal, export, runpod]
schema_version: 1.3
last_updated: "2026-10-17T20:55:18-03:00"
evidence: [fine_tuning/eval_results/post_sft_eval_s8_weighted.json, fine_tuning/scripts/runpod_sft_s8_weighted_f_gates.ps1]
---

# Weighted S8 SFT F gates (2026-10-17)

## Verdict
**FAIL** — do **not** promote Hub/Ollama `spurgeon-qa-v2`.

| Gate | Result |
|------|--------|
| refusal_accuracy | **0.46** (need ≥0.85) |
| echo_rate | 0.0 |
| corrupt_rate | 0.0 |
| im_end_stop_rate | 0.97 |
| leaked_turn_rate | 0.0 |
| groundedness | 4.12 |
| judge_model_consistent | true (gemini-3.5-flash-lite) |

## Artifacts
- LoRA: `fine_tuning/kaggle/runpod_sft_s8_weighted/sft_s8_weighted/adapter/lora/` SHA256 `e891731c9a71cb78c41f3cf8e1b7bbab54ea84c2ee4371d9105d773ae616f9dd`
- Report: `fine_tuning/eval_results/post_sft_eval_s8_weighted.json` (+ human review)
- Staging merge on volume `37lkz6dt50`: `/workspace/spurgeon_qa_s8w_merged_hf`

## Ops notes
- RunPod Secure 4090 (~$0.89/hr); Community 4090 stock was NONE.
- Groq judge HTTP 403 code 1010 from pod **and** local — use Gemini for judge.
- Remote script defaults `SFT_JUDGE_REMOTE=0` (generate on GPU, judge locally).
- SSH retry must not re-run full 100+100 generation after a judge failure.
- Orchestrator: `fine_tuning/scripts/runpod_sft_s8_weighted_f_gates.ps1`

## Orphan pod (2026-10-17 evening)
- After F-gates, MCP `list-pods` / `get-pod` showed empty/404, but **`runpodctl pod list` still showed** `5exy00fviuktb0` (`sft-s8w-f-gates`) RUNNING @ $0.89/hr.
- Deleted with `runpodctl pod delete 5exy00fviuktb0`. Always cross-check with runpodctl after MCP deletes.
- Vast: 0 instances.

## Next knob
Refusal is the only miss (worse than prior Hub v2 0.54). Raise refusal slice weight / retrain; keep groundedness path. No export until refusal ≥ 0.85.
