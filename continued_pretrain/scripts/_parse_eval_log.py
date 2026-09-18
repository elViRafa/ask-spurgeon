"""Parse multi-bucket eval losses from trainer_state.json checkpoints."""
import json
import sys
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    "continued_pretrain/kaggle/runpod_cpt_v3/s6_continue_b/checkpoints_sota"
)
files = sorted(
    root.rglob("trainer_state.json"),
    key=lambda p: int(p.parent.name.split("-")[1]) if "checkpoint-" in p.parent.name else 0,
)
steps: dict[int, dict[str, float]] = {}
best_step = None
best_metric = None
for p in files:
    data = json.loads(p.read_text(encoding="utf-8"))
    best_step = data.get("best_global_step") or best_step
    best_metric = data.get("best_metric") or best_metric
    for e in data.get("log_history", []):
        if "eval_spurgeon_loss" not in e:
            continue
        step = int(e.get("step") or e.get("global_step") or 0)
        steps[step] = {
            "spurgeon": float(e["eval_spurgeon_loss"]),
            "mix": float(e.get("eval_mix_loss", float("nan"))),
            "puritan": float(e.get("eval_puritan_loss", float("nan"))),
            "confession": float(e.get("eval_confession_loss", float("nan"))),
        }

if not steps:
    print("no eval rows in trainer_state files")
    sys.exit(0)

keys = sorted(steps)
print(f"from {len(files)} trainer_state files, {len(keys)} eval steps, max step {keys[-1]}")
print(f"HF best_model: step {best_step} eval_spurgeon_loss {best_metric:.4f}")
print(f"{'step':>6}  {'spurgeon':>8}  {'mix':>8}  {'puritan':>8}  {'conf':>8}")
for s in keys:
    if s % 100 != 0 and s < keys[-1] - 50:
        continue
    d = steps[s]
    mark = " *" if s == best_step else ""
    print(
        f"{s:6d}  {d['spurgeon']:8.4f}  {d['mix']:8.4f}  "
        f"{d['puritan']:8.4f}  {d['confession']:8.4f}{mark}"
    )
