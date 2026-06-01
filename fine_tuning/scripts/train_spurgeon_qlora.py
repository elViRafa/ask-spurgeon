#!/usr/bin/env python3
"""
Spurgeon QLoRA Fine-Tuning Script using Unsloth

This script trains a Llama-3.1-8B model with high fidelity to Spurgeon's text.

Designed to run on:
- Google Colab Pro (A100)
- RunPod / Vast.ai (A6000, A4000, etc.)
- Any machine with >= 24GB VRAM

Usage (example on Colab):
    !pip install unsloth
    python fine_tuning/scripts/train_spurgeon_qlora.py --dataset fine_tuning/data/spurgeon_synthetic.jsonl
"""

import os
import argparse
from pathlib import Path

# Unsloth must be imported before transformers
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template

from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments, DataCollatorForSeq2Seq

# =============================================================================
# CONFIGURATION (adjust as needed)
# =============================================================================

MODEL_NAME = "unsloth/llama-3.1-8b-instruct-bnb-4bit"   # Fast 4-bit version from Unsloth
MAX_SEQ_LENGTH = 4096
LOAD_IN_4BIT = True

# LoRA settings (good starting point for style transfer)
LORA_R = 64
LORA_ALPHA = 128
LORA_DROPOUT = 0.05

# Training hyperparameters
PER_DEVICE_BATCH_SIZE = 2
GRADIENT_ACCUMULATION_STEPS = 8
LEARNING_RATE = 1e-4
NUM_EPOCHS = 2
WARMUP_STEPS = 50


def formatting_func(examples, tokenizer):
    """Convert ChatML messages into training text."""
    texts = []
    for messages in examples["messages"]:
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False
        )
        texts.append(text)
    return {"text": texts}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, required=True, help="Path to JSONL dataset (ChatML format)")
    parser.add_argument("--output-dir", type=str, default="fine_tuning/outputs/spurgeon-8b-qlora")
    parser.add_argument("--save-merged", action="store_true", help="Also save merged 16-bit model at the end")
    args = parser.parse_args()

    print(f"Loading base model: {MODEL_NAME}")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        load_in_4bit=LOAD_IN_4BIT,
        dtype=None,  # Auto
    )

    # Add LoRA adapters
    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    # Apply Llama-3 chat template
    tokenizer = get_chat_template(tokenizer, chat_template="llama-3")

    # Load dataset
    print(f"Loading dataset from {args.dataset}")
    dataset = load_dataset("json", data_files=args.dataset, split="train")

    # Format dataset
    dataset = dataset.map(
        lambda examples: formatting_func(examples, tokenizer),
        batched=True,
        remove_columns=dataset.column_names
    )

    print(f"Dataset size: {len(dataset)} examples")

    # Training arguments
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=PER_DEVICE_BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
        warmup_steps=WARMUP_STEPS,
        num_train_epochs=NUM_EPOCHS,
        learning_rate=LEARNING_RATE,
        fp16=not LOAD_IN_4BIT,
        bf16=LOAD_IN_4BIT,
        logging_steps=10,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=42,
        save_strategy="epoch",
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        args=training_args,
        packing=False,
    )

    print("Starting training...")
    trainer.train()

    # Save LoRA adapter
    trainer.save_model(args.output_dir)
    print(f"LoRA adapter saved to: {args.output_dir}")

    if args.save_merged:
        print("Merging and saving 16-bit model...")
        model.save_pretrained_merged(
            f"{args.output_dir}-merged",
            tokenizer,
            save_method="merged_16bit",
        )
        print(f"Merged model saved to: {args.output_dir}-merged")


if __name__ == "__main__":
    main()
