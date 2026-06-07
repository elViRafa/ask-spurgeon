---
store_path: pretraining/bugs/sftconfig-pickle
title: "Fixed SFTConfig Pickling Mismatch on Kaggle"
summary: "Fixed SFTConfig Pickling Mismatch on Kaggle"
priority: medium
tags: [pretraining, unsloth, trl, sftconfig, pickle, bug-fix]
schema_version: 1.3
last_updated: "2026-06-07T06:33:34-04:00"
---

# Fixed SFTConfig Pickling Mismatch on Kaggle

During training checkpoint saving, PyTorch's `torch.save` serializes the trainer configuration `trainer.args`.
When running Unsloth on Kaggle, the dynamic compilation cache `/kaggle/working/unsloth_compiled_cache/UnslothSFTTrainer.py` re-imports or re-defines modules dynamically.
This causes a class identity mismatch: `sys.modules['trl.trainer.sft_config'].SFTConfig` is not the exact same class object as `trainer.args.__class__` anymore, triggering a `PicklingError`.

To resolve this:
1. Migrated Notebook B (`B_training.ipynb`) to use `trl.SFTConfig` directly.
2. In Cell 9 (Launch Training), added a metaprogramming fallback block right before calling `trainer.train()`:
   ```python
   import sys
   import trl
   if hasattr(trainer, "args") and trainer.args.__class__.__name__ == "SFTConfig":
       import trl.trainer.sft_config
       trl.trainer.sft_config.SFTConfig = trainer.args.__class__
       sys.modules["trl.trainer.sft_config"].SFTConfig = trainer.args.__class__
       trl.SFTConfig = trainer.args.__class__
   ```
This aligns the module entries with the instantiated class object, allowing the pickler to locate it successfully.
