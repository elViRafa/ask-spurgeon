import sys
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parent.parent.parent
    train_file = base_dir / "continued_pretrain" / "data" / "spurgeon_train.txt"
    holdout_file = base_dir / "continued_pretrain" / "data" / "spurgeon_holdout.txt"

    if not train_file.exists():
        print(f"Error: {train_file} does not exist. Run 05_build_corpus.py first.")
        sys.exit(1)

    print("Loading AutoTokenizer for Qwen/Qwen2.5-3B...")
    try:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B")
    except ImportError:
        print("Error: transformers is not installed in the current environment.")
        print("Please install it via: pip install transformers huggingface_hub")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading Qwen tokenizer: {e}")
        print("Attempting to fall back to GPT-2 tokenizer for estimation...")
        try:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained("gpt2")
        except Exception as fallback_err:
            print(f"Fallback tokenizer failed: {fallback_err}")
            sys.exit(1)

    # Validate train file
    train_text = train_file.read_text(encoding="utf-8")
    train_char_count = len(train_text)
    
    sample_size = min(500_000, train_char_count)
    sample_text = train_text[:sample_size]
    
    print(f"Tokenizing a sample of {sample_size:,} characters...")
    tokens = tokenizer(sample_text)["input_ids"]
    sample_token_count = len(tokens)
    
    token_to_char_ratio = sample_token_count / sample_size
    estimated_total_tokens = int(train_char_count * token_to_char_ratio)
    
    # Validate holdout file
    holdout_text = holdout_file.read_text(encoding="utf-8") if holdout_file.exists() else ""
    holdout_char_count = len(holdout_text)
    holdout_tokens_est = int(holdout_char_count * token_to_char_ratio) if holdout_text else 0

    print("=" * 60)
    print("Verification Metrics:")
    print("-" * 60)
    print(f"Train file size:      {train_char_count / 1024 / 1024:.2f} MB ({train_char_count:,} chars)")
    print(f"Sample token count:   {sample_token_count:,}")
    print(f"Token/Char ratio:     {token_to_char_ratio:.4f}")
    print(f"Est. Train tokens:    {estimated_total_tokens:,}")
    print(f"Est. Holdout tokens:  {holdout_tokens_est:,}")
    print("=" * 60)
    
    # Check delimiters
    delimiter = "<|endoftext|>"
    delim_count = train_text.count(delimiter)
    print(f"Found {delim_count} occurrences of {delimiter} in train file.")

if __name__ == "__main__":
    main()
