#!/usr/bin/env python3
"""
Local Synthetic Data Generator for Spurgeon Fine-Tuning (High Fidelity Version)

Generates training data by:
- Reading local sermon markdown files directly from data/chspurgeon-sermons (no DB needed).
- Extracting chunks containing key theological topics.
- Generating a realistic question and calling Groq (Llama-3.3-70b-versatile) to write
  a context-grounded response in Spurgeon's authentic voice.
- Retrying on Groq rate limits with exponential backoff.
"""

import os
import re
import json
import random
import argparse
import time
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm
from dotenv import load_dotenv

# Groq client
try:
    from groq import Groq
except ImportError:
    print("Please install groq: pip install groq")
    exit(1)

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TEACHER_MODEL = "llama-3.3-70b-versatile"   # Strong model for data generation

# Prompt designed for high fidelity
TEACHER_PROMPT = """You are Charles Haddon Spurgeon (1834–1892).

You are answering based **only** on the sermon excerpts provided in the CONTEXT section.

Rules (strict):
1. Use ONLY information that appears in the CONTEXT. Do not add outside knowledge, stories, or quotes.
2. If the context does not contain enough information to answer properly, say so clearly and humbly.
3. Speak in your natural voice: direct, warm, pastoral, full of Scripture, and vivid 19th-century language.
4. Keep answers reasonably concise while remaining rich in biblical truth.

CONTEXT:
{context}

QUESTION:
{question}

Answer in Spurgeon's voice, staying strictly faithful to the provided context:"""

QUESTION_TEMPLATES = [
    "What does Spurgeon say about {topic}?",
    "How does Spurgeon describe {topic}?",
    "What counsel does Spurgeon give regarding {topic}?",
    "According to Spurgeon, what is the importance of {topic}?",
    "How does Spurgeon explain {topic} in the Christian life?",
    "What warning does Spurgeon give about {topic}?",
    "What does Spurgeon teach concerning {topic}?",
]

TOPIC_KEYWORDS = [
    "faith", "prayer", "sin", "grace", "suffering", "election", "holiness",
    "the cross", "the Holy Spirit", "assurance", "repentance", "the church",
    "the love of Christ", "the sovereignty of God", "the resurrection",
    "the judgment", "the gospel", "sanctification", "justification"
]


def extract_chunks(text: str, chunk_size: int = 1200, min_chunk: int = 400, max_chunks: int = 3) -> List[str]:
    """Split sermon into clean chunks."""
    text = re.sub(r'\s+', ' ', text).strip()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""

    for sent in sentences:
        if len(current) + len(sent) > chunk_size and len(current) > min_chunk:
            chunks.append(current.strip())
            current = sent + " "
            if len(chunks) >= max_chunks:
                break
        else:
            current += sent + " "

    if current and len(current) > min_chunk and len(chunks) < max_chunks:
        chunks.append(current.strip())

    return chunks


def extract_topic(chunk: str) -> str:
    """Try to find a relevant topic from the chunk."""
    chunk_lower = chunk.lower()
    for topic in TOPIC_KEYWORDS:
        if topic in chunk_lower:
            return topic
    return random.choice(TOPIC_KEYWORDS)


def generate_spurgeon_response(question: str, context: str, groq_client: Groq, model: str = "llama-3.3-70b-versatile") -> str:
    """Call the teacher model with strict fidelity instructions, retrying on rate limits."""
    prompt = TEACHER_PROMPT.format(context=context, question=question)

    max_retries = 5
    base_delay = 2

    for attempt in range(max_retries):
        try:
            response = groq_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a careful theological writer who only uses the provided source material."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1200,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            err_str = str(e)
            if "rate_limit" in err_str.lower() or "429" in err_str or "limit_exceeded" in err_str.lower():
                delay = base_delay * (2 ** attempt)
                print(f"\n[RATE LIMIT] Rate limit hit. Error: {e}. Retrying in {delay}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(delay)
            else:
                print(f"\n[ERROR] Error generating response: {e}")
                delay = 2
                time.sleep(delay)
    
    return ""


def format_chatml_example(question: str, context: str, answer: str) -> Dict:
    """Format as Llama-3 ChatML for fine-tuning."""
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=1000, help="Number of examples to generate")
    parser.add_argument("--output", type=str, default="fine_tuning/data/spurgeon_train_1500.jsonl")
    parser.add_argument("--model", type=str, default="llama-3.3-70b-versatile", help="Model name to use for generation")
    args = parser.parse_args()

    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not found in environment.")
        return

    groq_client = Groq(api_key=GROQ_API_KEY)
    sermons_dir = Path("data/chspurgeon-sermons")

    if not sermons_dir.exists():
        print(f"ERROR: Sermon directory not found at {sermons_dir}")
        return

    sermon_files = list(sermons_dir.rglob("sermon*.md"))
    print(f"Found {len(sermon_files)} sermon files.")

    random.shuffle(sermon_files)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    examples_generated = 0
    pbar = tqdm(total=args.limit, desc="Generating Examples")

    with open(output_path, "w", encoding="utf-8") as f:
        for sermon_file in sermon_files:
            if examples_generated >= args.limit:
                break

            try:
                text = sermon_file.read_text(encoding="utf-8", errors="ignore")
                # Remove title/header if present
                text = re.sub(r'^#.*?\n', '', text, count=1)
                
                chunks = extract_chunks(text)
                for chunk in chunks:
                    if examples_generated >= args.limit:
                        break

                    topic = extract_topic(chunk)
                    question = random.choice(QUESTION_TEMPLATES).format(topic=topic)

                    answer = generate_spurgeon_response(question, chunk, groq_client, model=args.model)
                    if not answer or len(answer) < 50:
                        continue

                    example = format_chatml_example(question, chunk, answer)
                    f.write(json.dumps(example, ensure_ascii=False) + "\n")
                    f.flush()

                    examples_generated += 1
                    pbar.update(1)

                    # Basic throttle to respect RPM limits
                    time.sleep(1.0)

            except Exception as e:
                print(f"\n[FILE ERROR] Error processing {sermon_file.name}: {e}")
                continue

    pbar.close()
    print(f"\nDone! Successfully saved {examples_generated} examples to {output_path}")


if __name__ == "__main__":
    main()
