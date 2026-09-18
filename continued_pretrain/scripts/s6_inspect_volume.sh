#!/bin/bash
set -e
echo "=== DISK ==="
df -h /workspace | tail -1
echo "=== TRAIN ==="
pgrep -af train_cpt_sota.py || echo NO_TRAIN
echo "=== LAST STEP ==="
grep -oE '[0-9]+/4128' /workspace/cpt_train.log 2>/dev/null | tail -1 || echo none
echo "=== COMPLETION ==="
grep -E '4128/4128|COMPOSITE EARLY-STOP|Training completed|SOTA CPT v2 complete' /workspace/cpt_train.log 2>/dev/null | tail -3 || echo none
echo "=== CHECKPOINTS (last 8) ==="
ls -1d /workspace/checkpoints_sota/checkpoint-* 2>/dev/null | sort -V | tail -8
echo "=== CHECKPOINT FILES ==="
for n in 2050 2100 2107 2125 2150; do
  d="/workspace/checkpoints_sota/checkpoint-$n"
  if [ -d "$d" ]; then
    a=MISSING; [ -f "$d/adapter_model.safetensors" ] && a=YES
    python3 <<PY 2>/dev/null || echo "checkpoint-$n adapter=$a (no state)"
import json
d=json.load(open("$d/trainer_state.json"))
print("checkpoint-$n adapter=$a step=%s best=%s metric=%s" % (d.get("global_step"), d.get("best_global_step"), round(d.get("best_metric",0),4)))
PY
  fi
done
latest=$(ls -1d /workspace/checkpoints_sota/checkpoint-* 2>/dev/null | sort -V | tail -1)
if [ -n "$latest" ]; then
  n=$(basename "$latest")
  a=MISSING; [ -f "$latest/adapter_model.safetensors" ] && a=YES
  python3 -c "import json; d=json.load(open('$latest/trainer_state.json')); print('LATEST $n adapter='$a' step='+str(d.get('global_step'))+' best='+str(d.get('best_global_step'))+' metric='+str(round(d.get('best_metric',0),4)))" 2>/dev/null || echo "LATEST $n adapter=$a"
fi
echo "=== LORA ==="
ls -lh /workspace/theology_cpt_lora/adapter_model.safetensors 2>/dev/null || echo theology_cpt_lora MISSING
ls -lh /workspace/theology_cpt_run_config.json 2>/dev/null || echo run_config MISSING
echo "=== LOG TAIL ==="
tail -c 600 /workspace/cpt_train.log 2>/dev/null | tr '\r' '\n' | tail -4
