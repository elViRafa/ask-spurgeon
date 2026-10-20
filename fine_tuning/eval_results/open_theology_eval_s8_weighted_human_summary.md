# Open-theology chat eval — human summary

- Created: `2026-10-19T12:41:31.707203+00:00`
- Adapter SHA256: `e891731c9a71cb78c41f3cf8e1b7bbab54ea84c2ee4371d9105d773ae616f9dd`
- Eval set: `C:\Users\rafael\Projetos\search-sermons\fine_tuning\data\qa_open_theology\sft\open_theology_eval.jsonl` (n=40)
- Contract: `open_theology_chat_corpus_v1` (schema `open_theology_eval_1.1`)
- Release gate: **false** (informational only; does not unlock Hub/Ollama)
- Verdict label: **weak_not_useful_yet**
- Next FT knob: `rag_refusal_slice`

## Mechanical rates (gates)

- persona_violation_rate: 0.0
- false_refusal_rate: 0.025
- format_ok_rate: 0.975
- corrupt_rate: 0.0

## Citation diagnostics (not pass/fail)

- quote_in_passage_rate: 0.075
- heading_cited_rate: 0.0

## Judge means (1–5)

- provider/model: `gemini` / `gemini-3.5-flash-lite`
- correctness: 2.525 (gate)
- honesty: 2.525 (gate)
- persona_leakage: 5.0 (gate)
- citation_fidelity: 2.5 (diagnostic)

## Failure examples

### `eval-confession-002` failures=['false_refusal'] diagnostics=['quote_not_in_passage', 'missing_or_wrong_heading']

- Q: Which biblical passages are referenced by Gill in the systematic portion of his Body of Doctrinal Divinity as shown in the listed URLs?
- Heading: [Systematic — Gill Body Of Doctrinal Divinity]
- Prediction: I cannot access external URLs or specific content from them. However, I can provide general information about the biblical passages that are commonly referenced by John Gill in his "Body of Doctrinal Divinity." Gill was a Puritan theologian and his work is known for its extensive use of biblical citations. He often quotes from the Old and New Testaments to support his doctrinal points.

If you have specific passages or sections of Gill's work that you are interested in, feel free to share them, …
- Judge: {'correctness': 2, 'citation_fidelity': 3, 'persona_leakage': 5, 'honesty': 3} — The assistant failed to use the provided passage excerpt to answer the specific question about the listed URLs, falsely claiming it cannot access external information, though it maintained a clean kno

### `eval-puritan-004` failures=['format_fail'] diagnostics=['quote_not_in_passage', 'missing_or_wrong_heading']

- Q: According to Manton's Works Vol01, which Psalm chapter and verse is cited in entry number 452?
- Heading: [Manton — Works Vol01]
- Prediction: Psalm 119:176.
- Judge: {'correctness': 1, 'citation_fidelity': 1, 'persona_leakage': 5, 'honesty': 1} — The prediction incorrectly identifies the verse as Psalm 119:176, whereas the passage excerpt clearly shows entry number 452 corresponds to Psalm 11:7.
