#!/usr/bin/env python3
"""
Simple launcher for Spurgeon fine-tuning using the 1500-example dataset.

Usage:
    python fine_tuning/scripts/launch_training.py
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Spurgeon Fine-Tuning Launcher")
    parser.add_argument(
        "--config",
        type=str,
        default="fine_tuning/train_config.json",
        help="Path to the training configuration JSON file"
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    
    if not config_path.exists():
        print(f"Error: Configuration file not found at: {config_path}")
        sys.exit(1)
    
    with open(config_path) as f:
        config = json.load(f)
    
    dataset = config["dataset_path"]
    output_dir = config["output_dir"]
    model_name = config.get("model_name", "unsloth/llama-3.1-8b-instruct-bnb-4bit")
    chat_template = config.get("chat_template", "llama-3")
    
    print("=" * 60)
    print("Spurgeon Fine-Tuning Launcher")
    print("=" * 60)
    print(f"Config File : {args.config}")
    print(f"Base Model  : {model_name}")
    print(f"Template    : {chat_template}")
    print(f"Dataset     : {dataset}")
    print(f"Output      : {output_dir}")
    print(f"Epochs      : {config['training']['num_train_epochs']}")
    print(f"Batch size  : {config['training']['per_device_train_batch_size']} (accum {config['training']['gradient_accumulation_steps']})")
    print("=" * 60)
    
    # Build command
    cmd = [
        sys.executable,
        "fine_tuning/scripts/train_spurgeon_qlora.py",
        "--dataset", dataset,
        "--output-dir", output_dir,
        "--model-name", model_name,
        "--chat-template", chat_template,
    ]

    if "max_seq_length" in config:
        cmd += ["--max-seq-length", str(config["max_seq_length"])]
    if "load_in_4bit" in config:
        cmd += ["--load-in-4bit", str(config["load_in_4bit"]).lower()]

    lora = config.get("lora", {})
    if "r" in lora:
        cmd += ["--lora-r", str(lora["r"])]
    if "lora_alpha" in lora:
        cmd += ["--lora-alpha", str(lora["lora_alpha"])]
    if "lora_dropout" in lora:
        cmd += ["--lora-dropout", str(lora["lora_dropout"])]

    training = config.get("training", {})
    if "per_device_train_batch_size" in training:
        cmd += ["--batch-size", str(training["per_device_train_batch_size"])]
    if "gradient_accumulation_steps" in training:
        cmd += ["--grad-accum", str(training["gradient_accumulation_steps"])]
    if "learning_rate" in training:
        cmd += ["--learning-rate", str(training["learning_rate"])]
    if "num_train_epochs" in training:
        cmd += ["--num-epochs", str(training["num_train_epochs"])]
    if "warmup_steps" in training:
        cmd += ["--warmup-steps", str(training["warmup_steps"])]

    # Add --save-merged if specified in config or default to True
    if config.get("save_merged", True):
        cmd += ["--save-merged"]
    
    print("\nLaunching training with command:")
    print(" ".join(cmd))
    print("-" * 60)
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
