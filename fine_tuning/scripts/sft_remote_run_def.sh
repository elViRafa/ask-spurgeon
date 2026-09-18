#!/usr/bin/env bash
# Execute D then E then F notebooks. EXPORT stays False in F.
set -euo pipefail
export HF_HOME=/kaggle/working/hf_home
export PYTHONUNBUFFERED=1
cd /workspace/sft_nb

echo "===== D data prep ====="
jupyter nbconvert --to notebook --execute D_qa_data_prep_sota.ipynb \
  --ExecutePreprocessor.timeout=3600 \
  --output D_qa_data_prep_sota.executed.ipynb

echo "===== E training ====="
jupyter nbconvert --to notebook --execute E_qa_training_sota.ipynb \
  --ExecutePreprocessor.timeout=28800 \
  --output E_qa_training_sota.executed.ipynb

echo "===== F eval (EXPORT=False) ====="
jupyter nbconvert --to notebook --execute F_qa_eval_sota.ipynb \
  --ExecutePreprocessor.timeout=7200 \
  --output F_qa_eval_sota.executed.ipynb

echo "PIPELINE_DONE"
ls -la /kaggle/working/sft_run_config.json /kaggle/working/sft_eval_metrics.json /kaggle/working/spurgeon_qa_lora_v2/lora || true
