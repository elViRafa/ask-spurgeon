# Fine-Tuning Spurgeon — High Fidelity Generator

This folder contains everything needed to fine-tune a model that generates answers in Spurgeon’s voice **while staying highly faithful** to the actual source text.

## Recommended Starting Point

**Use the Google Colab notebook:**

→ `notebooks/Spurgeon_Fine_Tuning_Pipeline.ipynb`

This notebook walks you through the full pipeline:
- Synthetic data generation (grounded in your RAG)
- QLoRA training with Unsloth
- Merging and uploading to Hugging Face

## Folder Structure

```
fine_tuning/
├── FINE_TUNING_PLAN.md          # Full strategy, decisions, and roadmap
├── README.md                    # This file
├── data/                        # Where generated datasets go
├── scripts/
│   ├── generate_synthetic_data.py   # Creates high-fidelity training data
│   ├── train_spurgeon_qlora.py      # Main Unsloth QLoRA training script
│   └── evaluate.py                  # Evaluation harness (work in progress)
└── notebooks/
    └── Spurgeon_Fine_Tuning_Pipeline.ipynb   # ← Start here (Colab)
```

## Quick Local Commands – Using the Prepared 1500 Example Dataset

We have prepared a clean training set with **exactly 1500 examples**:

```bash
# Option 1: Use the launcher (recommended)
python fine_tuning/scripts/launch_training.py

# Option 2: Direct command
python fine_tuning/scripts/train_spurgeon_qlora.py \
    --dataset fine_tuning/data/spurgeon_train_1500.jsonl \
    --output-dir fine_tuning/outputs/spurgeon-8b-qlora-v1 \
    --save-merged
```

## Important Notes

- The entire approach prioritizes **textual fidelity** over pure stylistic imitation.
- The fine-tuned model is meant to be used **together with retrieval**, not standalone.
- See `FINE_TUNING_PLAN.md` for the full philosophy and evaluation strategy.

## Next Actions

1. Open the Colab notebook and run it.
2. Generate at least 1,000–2,000 high-quality examples.
3. Train a first small model.
4. Evaluate faithfulness rigorously.

Good luck — this has real potential to create something special.
