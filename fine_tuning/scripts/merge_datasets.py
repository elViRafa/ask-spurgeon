#!/usr/bin/env python3
"""
Dataset Merger and Deduplicator for Spurgeon Q&A Fine-Tuning
Combines multiple synthetic datasets (Groq, Ollama, OpenRouter, etc.),
removes duplicate examples, shuffles them, and splits them for training.
"""

import json
import random
from pathlib import Path
import argparse

def main():
    parser = argparse.ArgumentParser(description="Merge and deduplicate synthetic datasets.")
    parser.add_argument("--inputs", type=str, nargs="+", default=[
        "fine_tuning/data/spurgeon_train_1500.jsonl",
        "fine_tuning/data/spurgeon_train_ollama.jsonl",
        "fine_tuning/data/spurgeon_train_openrouter.jsonl"
    ], help="List of input JSONL files to merge")
    parser.add_argument("--output", type=str, default="fine_tuning/data/spurgeon_qa_train_final.jsonl", help="Final output merged JSONL file path")
    parser.add_argument("--val-split", type=float, default=0.05, help="Validation split ratio")
    args = parser.parse_args()
    
    merged_examples = []
    seen_conversations = set()
    
    print("Merging datasets:")
    for input_file in args.inputs:
        path = Path(input_file)
        if not path.exists():
            print(f" - [SKIP] {input_file} (file does not exist)")
            continue
            
        count = 0
        duplicates = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    messages = data.get("messages", [])
                    # Create a unique key based on the prompt/context + question to deduplicate
                    user_content = next((m["content"] for m in messages if m["role"] == "user"), "")
                    
                    if user_content in seen_conversations:
                        duplicates += 1
                        continue
                        
                    seen_conversations.add(user_content)
                    merged_examples.append(data)
                    count += 1
                except Exception as e:
                    pass
        print(f" - [LOAD] {input_file}: Loaded {count} examples (skipped {duplicates} duplicates)")
        
    total_examples = len(merged_examples)
    print(f"\nTotal unique examples combined: {total_examples}")
    
    if total_examples == 0:
        print("ERROR: No examples loaded. Nothing to save.")
        return
        
    # Shuffle the merged dataset to mix sources
    random.seed(42)
    random.shuffle(merged_examples)
    
    # Save the consolidated training file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for ex in merged_examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
            
    print(f"Saved merged dataset to: {output_path}")
    
    # If the user wants a split directly, let's output training and validation sets
    split_idx = int(total_examples * (1 - args.val_split))
    
    train_out = output_path.parent / "qa_train.jsonl"
    val_out = output_path.parent / "qa_val.jsonl"
    
    with open(train_out, "w", encoding="utf-8") as f:
        for ex in merged_examples[:split_idx]:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
            
    with open(val_out, "w", encoding="utf-8") as f:
        for ex in merged_examples[split_idx:]:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
            
    print(f"Split dataset:")
    print(f" - Train: {split_idx} examples -> {train_out}")
    print(f" - Val: {total_examples - split_idx} examples -> {val_out}")
    print("\nDataset preparation complete! You are ready to upload qa_train.jsonl and qa_val.jsonl to Kaggle.")

if __name__ == "__main__":
    main()
