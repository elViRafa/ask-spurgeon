import trl, inspect
from trl import SFTTrainer, SFTConfig
print("trl", trl.__version__)
print("SFTTrainer params:", list(inspect.signature(SFTTrainer.__init__).parameters))
print("SFTConfig params sample:", [k for k in inspect.signature(SFTConfig.__init__).parameters if "dataset" in k or "text" in k or "packing" in k or "max" in k][:40])
