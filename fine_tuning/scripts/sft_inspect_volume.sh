#!/bin/bash
set -e
echo "=== DISK ==="
df -h /workspace | tail -1
echo "=== TRAIN ==="
pgrep -af train_sft_sota.py || echo NO_TRAIN
echo "=== MERGE ==="
ls -lh /workspace/theology_cpt_v2_merged_hf/config.json 2>/dev/null || echo merged_hf MISSING
echo "=== LORA ==="
ls -lh /workspace/spurgeon_qa_lora_v2/lora/adapter_model.safetensors 2>/dev/null || echo sft_lora MISSING
ls -lh /workspace/sft_run_config.json 2>/dev/null || echo run_config MISSING
ls -lh /workspace/sft_eval_metrics.json 2>/dev/null || echo eval_metrics MISSING
echo "=== CPT S6 (do not touch) ==="
ls -lh /workspace/theology_cpt_lora/adapter_model.safetensors 2>/dev/null || echo theology_cpt_lora MISSING
echo "=== LOG TAIL ==="
tail -c 800 /workspace/sft_train.log 2>/dev/null | tr '\r' '\n' | tail -5
