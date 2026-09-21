#!/usr/bin/env bash
# In-place fix + C-eval on already-provisioned stack-isolation instance.
set -euo pipefail
source /workspace/miniforge3/etc/profile.d/conda.sh
conda activate unsloth_cpt_s5pin
unset LD_LIBRARY_PATH || true
export UNSLOTH_SKIP_TORCHVISION_CHECK=1
export EXPECTED_ADAPTER_SHA256=6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c
export CPT_EVAL_TRAIN_PROBE_DOCS=16
export REQUIRE_AMPERE=1
export CPT_WORK_ROOT=/workspace
export CPT_DATA_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export PYTHONUNBUFFERED=1

echo "Pinning torch 2.8.0 + torchvision 0.23.0; removing xformers (wants torch>=2.10)"
pip uninstall -y xformers 2>/dev/null || true
pip install -q --force-reinstall torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu126

python - <<'PY'
import torch
import torchvision
import unsloth
ver = tuple(int(x) for x in torch.__version__.split("+")[0].split(".")[:2])
print("torch", torch.__version__)
print("torchvision", torchvision.__version__)
print("unsloth", getattr(unsloth, "__version__", "?"))
assert ver == (2, 8), torch.__version__
print("FIX_OK")
PY

rm -f /workspace/cpt_eval.log /workspace/theology_cpt_eval_metrics.json
cd /workspace
python -u /workspace/eval_cpt_sota.py --preflight
echo PREFLIGHT_OK
python -u /workspace/eval_cpt_sota.py > /workspace/cpt_eval.log 2>&1
rc=$?
echo "$rc" > /workspace/c_eval_rc.txt
date -u > /workspace/c_eval_done.txt
echo "C_EVAL_EXIT=$rc"
tail -n 40 /workspace/cpt_eval.log || true
exit "$rc"
