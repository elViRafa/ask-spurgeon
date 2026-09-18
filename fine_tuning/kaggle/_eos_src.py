import inspect
from trl.trainer import sft_trainer
src = inspect.getsource(sft_trainer.SFTTrainer.__init__)
# print relevant eos section
for i, line in enumerate(src.splitlines()):
    if "eos" in line.lower() or "EOS" in line:
        print(f"{i}: {line}")
print("--- generation_config ---")
import json
from pathlib import Path
p = Path("/workspace/theology_cpt_v2_merged_hf/generation_config.json")
print(p.read_text()[:800] if p.exists() else "missing")
print("--- tokenizer config eos ---")
tc = Path("/workspace/theology_cpt_v2_merged_hf/tokenizer_config.json")
if tc.exists():
    import re
    text = tc.read_text(encoding="utf-8")
    for m in re.finditer(r'.{0,40}EOS.{0,40}|.{0,40}eos_token.{0,80}', text):
        print(m.group(0)[:120])
