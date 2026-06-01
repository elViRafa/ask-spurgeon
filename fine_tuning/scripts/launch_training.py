#!/usr/bin/env python3
"""
Simple launcher for Spurgeon fine-tuning using the 1500-example dataset.

Usage:
    python fine_tuning/scripts/launch_training.py
"""

import json
import subprocess
import sys
from pathlib import Path

def main():
    config_path = Path("fine_tuning/train_config.json")
    
    if not config_path.exists():
        print("Error: train_config.json not found!")
        sys.exit(1)
    
    with open(config_path) as f:
        config = json.load(f)
    
    dataset = config["dataset_path"]
    output_dir = config["output_dir"]
    
    print("=" * 60)
    print("Spurgeon Fine-Tuning Launcher")
    print("=" * 60)
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
        "--save-merged"
    ]
    
    print("\nLaunching training...")
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
