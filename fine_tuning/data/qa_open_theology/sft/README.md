# Open-theology SFT slice (`open_theology`)

A side SFT dataset: knowledge-assistant Q&A on Spurgeon, the Puritans, and the
confessions/catechisms, **without a RAG CONTEXT turn**. A teacher model (mostly groq
`openai/gpt-oss-120b`, some `gemini-2.5-flash`) wrote each Q/A pair from one source passage.
Each answer carries a verbatim quote from that passage and ends with the bracketed catalog
heading, e.g. `[Boston — Fourfold State]` or `[Sermon 2806 — "Jesus Our Lord"]`.

Generation history, checks and open decisions: see `../README_HANDOFF.md`.

## Keep it separate
- Do **not** merge into `qa_mix_train.jsonl` / `qa_test_frozen.jsonl` or the RAG mix, and do
  not run `build_qa_mix_v2.py` on it. The RAG mix teaches "answer only from CONTEXT"; this slice
  teaches open answers with a different system prompt.
- In the SFT recipe, load it as **its own dataset with its own sampling weight** next to the
  existing mix (e.g. interleave/concatenate with a weight), and report its eval separately.

## Files
| file | what |
|---|---|
| `open_theology_train.jsonl` | train rows |
| `open_theology_eval.jsonl` | held-out eval rows (never train on them). May be partial; see manifest |
| `manifest.json` | counts by bucket/teacher, sha256 of outputs and sources, source commit, generator version, exclusions, validation |
| `excluded_ids.json` | rows left out on purpose, with reasons. Delete an entry and re-export to reinstate it |
| `meta_wording_ids.json` | rows that say "the passage" / "the text" / "the excerpt" / "this quote". Kept; flagged so you can filter or down-weight |

## Row format
Same shape as the side slices already in `qa_mix_train.jsonl` (`id`, `slice`, `messages`):
```json
{"id": "train-puritan-144", "slice": "open_theology",
 "messages": [{"role": "system", "content": "<THEOLOGY_CHAT_SYSTEM_PROMPT>"},
              {"role": "user", "content": "<question>"},
              {"role": "assistant", "content": "<answer ... [Heading]>"}]}
```
- Single turn; train on the assistant turn only (standard chat SFT masking).
- System prompt = `config.THEOLOGY_CHAT_SYSTEM_PROMPT` (sha256 in the manifest). It differs
  from the RAG `SPURGEON_SFT_SYSTEM_PROMPT` on purpose; keep both prompts as they are.
- No extra fields; source passages and teacher metadata stay in `../accepted.jsonl` (`meta`).

## Regenerate
From the repo root (rerun any time, e.g. when the remaining eval jobs land):
```
python fine_tuning/scripts/export_open_theology_sft.py            # dry: validate + print counts
python fine_tuning/scripts/export_open_theology_sft.py --apply    # rewrite sft/
python -m pytest -q fine_tuning/scripts/test_export_open_theology_sft.py
```
The export rebuilds everything from `../accepted.jsonl` and `../eval_accepted.jsonl`. It applies
`excluded_ids.json`, drops duplicate ids and questions, re-runs `open_theology_qa_checks`, checks
that each answer ends with its catalog heading, drops holdout hits (mix_v7 fingerprints and
Spurgeon holdout sermons), and drops train rows that share a work, passage or question with eval.
It exits 1 if any row is invalid or hits a holdout.
