#!/usr/bin/env python3
"""
Synthetic Q&A Generation Script for Charles Spurgeon Fine-Tuning
Generates high-quality, diverse, context-grounded Q&A pairs directly from sermon chunks.
"""

import os
import re
import json
import random
import time
import argparse
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq client
try:
    from groq import Groq
except ImportError:
    print("Please install groq: pip install groq")
    exit(1)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY not found in environment. The script will fail when making API calls.")

# Project configuration
TEACHER_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are a Charles Spurgeon scholar building a training dataset for a Q&A assistant.
Given a passage from one of Charles Spurgeon's sermons, generate exactly 1 or 2 specific question-answer pairs based strictly on the passage.

Rules:
1. The questions must be specific, natural, and answerable ONLY from the provided passage. Avoid generic templates (e.g. do NOT ask "What does Spurgeon say about faith?" instead ask a detail-oriented question like "Why does Spurgeon compare faith to an empty hand?").
2. The answers must be grounded 100% in the passage. Write the answers in Spurgeon's authentic voice and register: warm, pastoral, vivid, and full of 19th-century theological terms, but directly answering the user's question.
3. Return ONLY a JSON array with the generated pairs. Do not include markdown fences, code blocks, or extra text.

Example format:
[
  {
    "question": "What comparison does Spurgeon make to illustrate the weakness of the arm of flesh?",
    "answer": "My brethren, the arm of flesh is a broken reed that will pierce you if you lean upon it. It is as a sandy foundation that crumbles beneath the tempest, leaving the builder utterly ruined. Therefore, look not to man, but to the living God."
  }
]"""

def clean_sermon_text(text: str) -> str:
    """Normalize whitespace and remove markdown heading styling."""
    text = re.sub(r'#+\s+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def chunk_sermon(text: str, chunk_size: int = 1200, chunk_overlap: int = 400, min_chunk: int = 400) -> list[str]:
    """Split sermon into overlapping text chunks."""
    chunks = []
    start = 0
    while start < len(text) - min_chunk:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if len(chunk) >= min_chunk:
            chunks.append(chunk)
        start += chunk_size - chunk_overlap
    return chunks

def call_groq_with_retry(groq_client: Groq, prompt: str, max_retries: int = 5) -> str:
    """Call Groq API with exponential backoff on rate limits."""
    model = TEACHER_MODEL
    base_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = groq_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            err_str = str(e)
            if "rate_limit" in err_str.lower() or "429" in err_str or "limit_exceeded" in err_str.lower():
                delay = base_delay * (2 ** attempt)
                # Try fallback model on later attempts to salvage execution
                if attempt >= 2:
                    model = FALLBACK_MODEL
                time.sleep(delay)
            else:
                time.sleep(2)
                
    return ""

def format_chatml(question: str, context: str, answer: str) -> dict:
    """Format into standard ChatML format expected by training notebooks."""
    return {
        "messages": [
            {
                "role": "system",
                "content": "You are Charles Haddon Spurgeon. Answer using only the information in the provided CONTEXT. Stay very close to the actual text."
            },
            {
                "role": "user",
                "content": f"CONTEXT:\n{context}\n\nQUESTION:\n{question}"
            },
            {
                "role": "assistant",
                "content": answer
            }
        ]
    }

def main():
    parser = argparse.ArgumentParser(description="Generate high-quality Spurgeon Q&A dataset.")
    parser.add_argument("--limit", type=int, default=1000, help="Number of Q&A pairs to generate")
    parser.add_argument("--output", type=str, default="fine_tuning/data/spurgeon_train_1500.jsonl", help="Output JSONL file path")
    args = parser.parse_args()
    
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not set in environment.")
        return
        
    groq_client = Groq(api_key=GROQ_API_KEY)
    
    sermons_dir = Path("data/chspurgeon-sermons")
    holdout_dir = Path("data/chspurgeon-holdout")
    
    if not sermons_dir.exists():
        print(f"ERROR: Sermons directory {sermons_dir} does not exist.")
        return
        
    holdout_stems = set()
    if holdout_dir.exists():
        holdout_stems = {p.stem for p in holdout_dir.rglob("*.md")}
        print(f"Loaded {len(holdout_stems)} holdout sermon names to skip.")
        
    sermon_files = [p for p in sermons_dir.rglob("*.md") if p.stem not in holdout_stems]
    print(f"Found {len(sermon_files)} training sermons to process.")
    
    # Extract all chunks
    all_chunks = []
    for file in tqdm(sermon_files[:150], desc="Chunking sermons"): # Sample first 150 sermons to get plenty of chunks
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
            # Remove title headers
            text = re.sub(r'^#.*?\n', '', text, count=1)
            cleaned = clean_sermon_text(text)
            chunks = chunk_sermon(cleaned)
            for chunk in chunks:
                all_chunks.append((file.name, chunk))
        except Exception as e:
            continue
            
    print(f"Extracted {len(all_chunks)} total chunks.")
    random.seed(42)
    random.shuffle(all_chunks)
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    generated_count = 0
    pbar = tqdm(total=args.limit, desc="Generating QA pairs")
    
    # Standard query list for generating unanswerable / honest refusals (controlled at ~7% of dataset)
    # We will mix these in intentionally
    refusal_queries = [
        "What did Spurgeon think about Charles Darwin's theory of evolution?",
        "What is Spurgeon's view on modern Christian rock music?",
        "How does Spurgeon explain the process of building the Metropolitan Tabernacle using steel frames?",
        "What does Spurgeon say about the sovereignty of God in modern electronic media?",
        "How did Spurgeon describe his trip to the United States in 1885?",
        "What did Spurgeon teach about the importance of Sunday School classrooms in the 21st century?",
        "What warning does Spurgeon give regarding the use of telephone lines in the church?"
    ]
    
    with open(output_path, "w", encoding="utf-8") as out_f:
        for filename, chunk in all_chunks:
            if generated_count >= args.limit:
                break
                
            # Intentionally inject an unanswerable example at ~7% probability
            is_refusal = random.random() < 0.07
            
            if is_refusal:
                # Pair with an unanswerable query
                question = random.choice(refusal_queries)
                
                # Ask teacher LLM to generate a grounded refusal in Spurgeon's voice
                refusal_prompt = f"""CONTEXT:
{chunk}

QUESTION:
{question}

Write a brief response in Spurgeon's authentic voice and register, politely explaining that the provided context does not address this question. Do not refer to the prompt instructions. Keep it to 2-3 sentences."""
                
                # Call LLM with simple system instructions
                for attempt in range(3):
                    try:
                        response = groq_client.chat.completions.create(
                            model=TEACHER_MODEL,
                            messages=[
                                {"role": "system", "content": "You are Charles Spurgeon. Answer using only the provided context. If it is not present, explain so in your pastoral voice."},
                                {"role": "user", "content": refusal_prompt}
                            ],
                            temperature=0.5,
                            max_tokens=300
                        )
                        answer = response.choices[0].message.content.strip()
                        break
                    except Exception:
                        time.sleep(2)
                        answer = ""
                
                if answer:
                    example = format_chatml(question, chunk, answer)
                    out_f.write(json.dumps(example, ensure_ascii=False) + "\n")
                    out_f.flush()
                    generated_count += 1
                    pbar.update(1)
                continue
                
            # Regular grounded QA generation
            qa_json_str = call_groq_with_retry(groq_client, f"Sermon excerpt:\n{chunk}\n\nGenerate Q&A:")
            if not qa_json_str:
                continue
                
            # Clean JSON string (remove markdown wrappers if generated despite prompt rules)
            cleaned_json = re.sub(r'^```json\s*', '', qa_json_str)
            cleaned_json = re.sub(r'\s*```$', '', cleaned_json).strip()
            
            try:
                pairs = json.loads(cleaned_json)
                if not isinstance(pairs, list):
                    pairs = [pairs]
                    
                for pair in pairs:
                    if generated_count >= args.limit:
                        break
                    q = pair.get("question", "").strip()
                    a = pair.get("answer", "").strip()
                    
                    if q and a and len(q) > 15 and len(a) > 40:
                        example = format_chatml(q, chunk, a)
                        out_f.write(json.dumps(example, ensure_ascii=False) + "\n")
                        out_f.flush()
                        generated_count += 1
                        pbar.update(1)
                        
            except Exception:
                continue
                
            # Rate limit throttle
            time.sleep(0.8)
            
    pbar.close()
    print(f"\nSuccessfully generated {generated_count} high-quality Q&A examples.")

if __name__ == "__main__":
    main()
