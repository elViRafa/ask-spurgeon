# Fix S3 label masking for multi-turn rows in train_sft_sota.py (weighted SFT S8 crash)

## Problem
Weighted SFT S8 on Vast (Netherlands 4090, instance 56100982, 2026-10-15) crashed before step 1:
`AssertionError: S3 FAIL row 5: user turn leaked into labels` at `_assert_s3_row` (train_sft_sota.py:607), called from `_audit_s3_dataset` (L822) in `_train_peft`.

Logs: `fine_tuning\kaggle\vast_sft_s8_weighted\host3_56100982_sft_train.log`.
The CRLF fix works (setup ran). Other walk-away checks passed (3822 rows kept, 0 over 4608).

## Root cause
`_mask_assistant_labels` (train_sft_sota.py ~L553-583) starts supervising at the FIRST `<|im_start|>assistant\n` marker.
100 of the 3264 rows in qa_mix_train.jsonl are multi-turn (system, user, assistant, user, assistant). The second user turn, with the CONTEXT block, lands inside the supervised span. The audit is right; the mask is wrong.

Row 5 = first multi-turn RAG row after `build_weighted_message_rows` (RAG rows first, then 558 open-theology, then `random.Random(3407).shuffle`). All 558 open-theology rows are system/user/assistant and fine.
Earlier peft runs on this mix were probably affected, because the old S3 check only checked row 0.
The unsloth path uses `train_on_responses_only` (L1030) and is unaffected.

## Fix (one knob, only `_mask_assistant_labels`)
Use the LAST assistant marker. A missing marker still means all labels -100 and the row is dropped.
Alternative (more code): supervise every assistant span through its `<|im_end|>`.
- Do NOT drop the 100 rows.
- Do NOT loosen the audit.
- Do NOT shorten seq length (4608).

## Tests
Add `fine_tuning/tests/test_sft_s3_mask_all_rows.py` (no GPU):
1. Load the Qwen tokenizer.
2. Build the 3822 rows with seed 3407, apply the template, truncate to 4608.
3. Run `_mask_assistant_labels`, then `_audit_s3_dataset` on a Dataset with `input_ids` and `labels`; assert zero failures.
4. Add a synthetic system/user/assistant/user/assistant case.
5. Assert multi-turn count > 0.

## Also
- Add `*.ps1 text eol=lf` to `.gitattributes` so `test_orchestrator_strips_cr_from_remote_ssh_scripts` passes on pc1 (autocrlf produced CRLF in the working tree; blob is LF).
- `vast_destroy.ps1` reported "nothing to destroy" because it could not find the instance id in the session file (destroyed via CLI instead). Fix if simple.

## Rules
- Cursor fixes scripts only and never rents a GPU.
- Do not stage `fine_tuning/data/qa_open_theology/`.
- Commit and push to main.