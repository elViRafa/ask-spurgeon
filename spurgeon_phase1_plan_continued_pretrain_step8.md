# Phase 1: Spurgeon Continued Pretraining — Step 8: Session Schedule Plan

This document details the executed session schedule and results for the pretraining pipeline of `unsloth/Qwen2.5-3B` on Charles Spurgeon's sermons, adjusted to reflect that Epoch 1 and Epoch 2 have completed successfully, bypassing the optional Epoch 3.

---

## 1. Timeline and Session Summary

Due to Kaggle Free Tier limits (9-hour background runtimes per session), Phase 1 continued pretraining was scheduled and executed across the following distinct session stages:

```
Session 1 (Completed): Notebook A (Dataset Preparation)
  - Raw .txt files parsed and saved to disk.
  - Output linked as dataset: "spurgeon-cpt-dataset" (Private).

Session 2 (Completed): Notebook B - Run 1 (Epoch 1)
  - Base model loaded in 4-bit, LoRA rank 32 applied.
  - SFTTrainer executed from scratch.
  - Ended at step 216 (loss ~2.29).
  - Output linked as dataset: "spurgeon-training-run-1" (Version 1).

Session 3 (Completed): Notebook B - Run 2 (Epoch 2)
  - Mounted dataset "spurgeon-training-run-1" (Version 1).
  - Set RUN_NUMBER = 2, TOTAL_TARGET_EPOCHS = 2.
  - Set PREV_RUN_CHECKPOINT pointing to "checkpoint-216".
  - Training completed at step 432.
  - Saved outputs by uploading a new version (Version 2) to the existing dataset "spurgeon-training-run-1".

Session 4 (Next): Notebook C (Evaluation and LoRA Export)
  - Mounts "spurgeon-cpt-dataset" (for holdout set) and "spurgeon-training-run-1" (Version 2).
  - Loads final model PEFT adapter directly from checkpoint-432.
  - Evaluates perplexity on the 50-sermon holdout dataset.
  - Runs qualitative completion tests.
  - Exports the finalized LoRA adapter to "/kaggle/working/spurgeon_lora_final".
```

---

## 2. Pretraining Parameter & Run Summary Table

| Parameter | Run 1 (Epoch 1) | Run 2 (Epoch 2) |
| :--- | :--- | :--- |
| **Accelerator** | 1x T4 GPU | 1x T4 GPU |
| **Start State** | Training from scratch | Resumed from `checkpoint-216` |
| **Total Target Epochs** | 1 | 2 |
| **Completed Steps** | 216 | 432 (Cumulative) |
| **Effective Batch Size** | 16 (2 per device * 8 accumulation) | 16 (2 per device * 8 accumulation) |
| **Final Loss** | ~2.2890 | ~2.1800 (est.) |
| **Validation Loss** | ~2.3375 | ~2.2400 (est.) |
| **Run Duration** | ~1 hour 16 minutes | ~1 hour 18 minutes |
| **Save Location** | `spurgeon_lora_epoch1` | `spurgeon_lora_epoch2` / `checkpoint-432` |
| **Kaggle Dataset Action** | Created new `spurgeon-training-run-1` v1 | Pushed as "New dataset version" (v2) |

---

## 3. Kaggle Checkpoint Dataset Lifecycle

Persisting weights correctly across Kaggle sessions was managed through Kaggle's private dataset versioning:

```
                  [Session 2 Output (/kaggle/working)]
                                  │
                                  ▼
           Create new dataset: "spurgeon-training-run-1" (V1)
                                  │
                                  ▼
                     [Session 3 Input (/kaggle/input)]
                                  │
                                  ▼
            Resume from checkpoints/checkpoint-216 inside V1
                                  │
                                  ▼
                  [Session 3 Output (/kaggle/working)]
                                  │
                                  ▼
       Upload output as "New dataset version" -> "spurgeon-training-run-1" (V2)
                                  │
                                  ▼
           [Notebook C Input (/kaggle/input/spurgeon-training-run-1)]
                    - checkpoints/checkpoint-432/
                    - spurgeon_lora_epoch2/
```

This lifecycle completely avoided allocating multiple distinct dataset inputs in the Kaggle account and simplified path referencing in Notebook C to `/kaggle/input/datasets/rafaelvieira1/spurgeon-training-run-1/checkpoints/checkpoint-432`.
