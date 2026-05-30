# RAG Evaluation Tests for "Ask Spurgeon"

This folder contains an evaluation framework for testing the quality of the Spurgeon RAG system.

## Recommended: Use the top-level `eval.py`

For convenience, use the root-level script:

```bash
# Full evaluation with LLM-as-Judge
python eval.py

# Quick test
python eval.py --limit 5

# Compare two prompt variants
python eval.py --compare default strict

# Compare and save results
python eval.py --compare default strict --save comparison.json
```

See `python eval.py --help` for all options.

## Test Questions

`rag_test_questions.py` contains 20 curated questions inspired by real theological inquiries from [GotQuestions.org](https://www.gotquestions.org/content.html), tailored to Spurgeon's preaching themes:

- Direct famous sermons (Immutability of God, etc.)
- Core doctrines (sovereignty + responsibility, election, perseverance)
- Practical pastoral topics (prayer, suffering, assurance, fighting sin)
- Bible passage interpretation
- Edge cases to test honest "I don't know" behavior

## Running the Evaluator Directly (Advanced)

```bash
# From project root, with venv activated
python tests/evaluate_rag.py

# Run only the first 5 questions (faster for iteration)
python tests/evaluate_rag.py --limit 5

# Save full results to JSON for analysis
python tests/evaluate_rag.py --save results/run_2026-05-30.json
```

## What the Evaluator Does

For each question it:
1. Retrieves the top-k most relevant chunks from Qdrant.
2. Generates an answer using the exact same prompt style as the live app.
3. Records:
   - Retrieved sermons + scores
   - Full generated answer
   - Timing (retrieval + generation)
   - Simple heuristic checks (did it cite sources? Did it admit limitations?)

## Current Known Limitations / Areas for Improvement

- The evaluator currently relies on manual review of the generated answers.
- Future work could add:
  - LLM-as-judge scoring for faithfulness and helpfulness.
  - Automatic "relevant sermon" matching using metadata.
  - Comparison between different prompt versions or retrieval strategies.

## Recent Improvements Made

- Strengthened system prompt to be stricter about staying in context and clearly admitting limitations.
- Fixed file discovery bug in ingestion (now properly indexes all 3,500+ sermons).
- Created this evaluation framework to enable systematic testing and iteration.

Run the evaluator regularly after major changes to the prompt, chunking strategy, or retrieval parameters.
