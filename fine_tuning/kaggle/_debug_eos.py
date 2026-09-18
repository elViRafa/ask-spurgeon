#!/usr/bin/env python3
import os
os.environ.setdefault("HF_HOME", "/workspace/hf_home")

import unsloth  # noqa: F401 — import before trl
from unsloth import FastLanguageModel
from trl import SFTConfig, SFTTrainer

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="/workspace/theology_cpt_v2_merged_hf",
    max_seq_length=4096,
    dtype=None,
    load_in_4bit=True,
)
print("tok class", type(tokenizer))
print("tok.eos", repr(getattr(tokenizer, "eos_token", None)), getattr(tokenizer, "eos_token_id", None))
for t in ["<|im_end|>", "<|endoftext|>", "<EOS_TOKEN>"]:
    print("id", t, tokenizer.convert_tokens_to_ids(t))

args = SFTConfig(
    output_dir="/tmp/sft_dbg",
    per_device_train_batch_size=1,
    max_steps=1,
    dataset_text_field="text",
    packing=False,
    max_length=512,
    eos_token="<|im_end|>",
    report_to="none",
)
print("args.eos_token", repr(args.eos_token))
print("args keys eos", {k: getattr(args, k) for k in dir(args) if "eos" in k.lower()})

# Minimal dataset
from datasets import Dataset
ds = Dataset.from_dict({"text": ["<|im_start|>user\nhi<|im_end|>\n<|im_start|>assistant\nhello<|im_end|>\n"]})
try:
    trainer = SFTTrainer(model=model, args=args, train_dataset=ds, processing_class=tokenizer)
    print("SFTTrainer OK")
except Exception as e:
    print("SFTTrainer FAIL", type(e), e)
