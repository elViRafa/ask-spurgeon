# Open-theology chat eval — human summary

- Created: `2026-10-20T15:51:13.431656+00:00`
- Adapter SHA256: `a34d288652b52b840b1a40bdb5173d49348010830ceab026dc06949478cc49c0`
- Eval set: `C:\Users\rafael\Projetos\search-sermons\fine_tuning\data\qa_open_theology\sft\open_theology_eval.jsonl` (n=40)
- Contract: `open_theology_chat_corpus_v1` (schema `open_theology_eval_1.1`)
- Release gate: **false** (informational only; does not unlock Hub/Ollama)
- Verdict label: **weak_not_useful_yet**
- Next FT knob: `rag_refusal_slice`

## Mechanical rates (gates)

- persona_violation_rate: 0.0
- false_refusal_rate: 0.0
- format_ok_rate: 1.0
- corrupt_rate: 0.0

## Citation diagnostics (not pass/fail)

- quote_in_passage_rate: 0.1
- heading_cited_rate: 0.0

## Judge means (1–5)

- provider/model: `gemini` / `gemini-3.5-flash-lite`
- correctness: 2.65 (gate)
- honesty: 2.5 (gate)
- persona_leakage: 5.0 (gate)
- citation_fidelity: 2.475 (diagnostic)

## Failure examples

_No mechanical failures (persona / false refusal / format)._
