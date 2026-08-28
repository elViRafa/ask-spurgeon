# Kaggle runbook — SFT v2 (Qwen3.5-4B-Base)

Operator path on **1× T4 16 GB**. CPT must pass GATE-0 for the final SFT run; dev runs use stock base.

## 0. Local prep

```bash
python fine_tuning/scripts/build_qa_mix.py
python fine_tuning/scripts/12_package_kaggle_qa_mix.py
python fine_tuning/scripts/_gen_sota_sft_notebooks.py
```

Upload `fine_tuning/data/kaggle_upload/spurgeon-qa-mix-v1.zip` → Kaggle dataset **`spurgeon-qa-mix-v1`**.

## 1. Notebook D_sota — data prep

1. Mount `spurgeon-qa-mix-v1`
2. Run [`D_qa_data_prep_sota.ipynb`](notebooks/D_qa_data_prep_sota.ipynb)
3. Confirm S1 token audit: <2% examples over 4096 tokens
4. Outputs: `qa_dataset_train/` + `qa_dataset_val/` in `/kaggle/working`

Optional: save as Kaggle dataset `spurgeon-qa-dataset-v1` for reuse.

## 2. Notebook E_sota — training (stock base dry-run)

1. Mount qa mix (and optional prebuilt dataset)
2. GPU T4 ×1, Internet on
3. Config: `USE_CPT_MERGE = False`, `BASE_MODEL = unsloth/Qwen3.5-4B-Base`
4. Run S2/S3 cells; train 2 epochs
5. Save adapter to `/kaggle/working/spurgeon_qa_lora_v2/lora` + `sft_run_config.json`

VRAM ladder: batch 1×16 → seq 3072 → LoRA r=16.

## 3. Notebook F_sota — eval (EXPORT=False)

1. Load adapter + frozen `qa_test_frozen.jsonl`
2. Run greedy battery; check corrupt_rate ≈ 0, refusal accuracy
3. Keep **`EXPORT = False`** until §5 gates pass

## 4. GATE-0 final run

After CPT publishes `theology-cpt-v2` with `theology_cpt_v2_merged_hf/`:

1. In E_sota + F_sota: `USE_CPT_MERGE = True`
2. `BASE_MODEL = /kaggle/input/datasets/rafaelvieira1/theology-cpt-v2/theology_cpt_v2_merged_hf`
3. Retrain 2 epochs; re-run F_sota

## 5. Export (only after gates)

1. F_sota: `EXPORT = True` → merge 16-bit HF
2. Convert GGUF f16 + Q4_K_M (Unsloth / llama.cpp)
3. Download to `fine_tuning/models/spurgeon-qa-v2.*.gguf`
4. Upload: `python fine_tuning/scripts/upload_sft_gguf_to_hf.py`
5. Ollama:
   ```bash
   ollama create spurgeon-qa-v2 -f fine_tuning/models/Modelfile.qwen35-spurgeon-qa-v2
   python fine_tuning/scripts/smoke_test_ollama.py --model spurgeon-qa-v2
   ```
6. App `.env`: `LLM_PROVIDER=openai`, `CUSTOM_LLM_MODEL=spurgeon-qa-v2`

## Success gates (FN plan §5)

- Faithfulness judge ≥ 4.0/5 on answerable set
- Refusal accuracy ≥ 85%
- Structural echo ≤ 2%
- Ollama smoke: zero `pist`/`spep`/Chinese junk at temperature 0

## Companion

- CPT runbook: [`../continued_pretrain/KAGGLE_RUNBOOK_V2.md`](../continued_pretrain/KAGGLE_RUNBOOK_V2.md)
- Plan: [`notebooks/PLAN_FABLE5_TO_IMPROVE_FN.md`](notebooks/PLAN_FABLE5_TO_IMPROVE_FN.md)
