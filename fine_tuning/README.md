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

## Using in Google Colab

The file `spurgeon_train_1500.jsonl` is **not automatically available** when you clone the repo in Colab (because large data files bloat git).

**Best ways to use it in Colab:**

1. **Easiest**: After cloning the repo in Colab, upload `fine_tuning/data/spurgeon_train_1500.jsonl` using the Files sidebar (click the folder icon → Upload).

2. **Recommended for repeated use**: Upload the file to your Google Drive, then mount Drive and load it from there.

3. **Best long-term**: Upload the dataset to the Hugging Face Datasets Hub and download it with `load_dataset("your-username/spurgeon-1500")`.

See the notebook `fine_tuning/notebooks/Spurgeon_1500_Training_Colab.ipynb` — it already has clear instructions for this.

## Running the Fine-Tuned Model in Ollama

If you already published your quantized Gemma 4 model to Hugging Face, you can import it into Ollama with the provided Modelfile.

```bash
huggingface-cli download rafaelvieirar1r/gemma-4-12b-spurgeon-generator Spurgeon-Gemma4-12B-Q4_K_M.gguf --local-dir fine_tuning/models --local-dir-use-symlinks False
cd fine_tuning/models
ollama create spurgeon-gemma4 -f Modelfile.gemma4
ollama run spurgeon-gemma4
```

Then point the main app to Ollama:

```env
LLM_PROVIDER=openai
CUSTOM_LLM_BASE_URL=http://localhost:11434/v1
CUSTOM_LLM_API_KEY=ollama
CUSTOM_LLM_MODEL=spurgeon-gemma4
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
