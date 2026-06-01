#!/usr/bin/env python3
"""
Autonomous Local Dataset Generator for Spurgeon Fine-Tuning

Generates a larger synthetic dataset WITHOUT external API calls.
Focuses on high textual fidelity by heavily grounding answers in actual sermon text.

This is a practical way to bootstrap a bigger dataset when Groq/Claude calls are not available.
"""

import os
import json
import random
import re
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm

# =============================================================================
# CONFIG
# =============================================================================

SERMONS_DIR = Path("data/chspurgeon-sermons")
OUTPUT_FILE = Path("fine_tuning/data/spurgeon_synthetic_large.jsonl")
MAX_EXAMPLES = 1500          # Target size
SAMPLES_PER_SERMON = 2       # How many examples per sermon
CHUNK_SIZE = 1200            # Characters per chunk
MIN_CHUNK_LENGTH = 400

# Simple question templates (we will fill them with real content)
QUESTION_TEMPLATES = [
    "What does Spurgeon say about {topic}?",
    "How does Spurgeon describe {topic}?",
    "What counsel does Spurgeon give regarding {topic}?",
    "According to Spurgeon, what is the importance of {topic}?",
    "How does Spurgeon explain {topic} in the Christian life?",
    "What warning does Spurgeon give about {topic}?",
    "What does Spurgeon teach concerning {topic}?",
]

# Topics we will try to extract from text
TOPIC_KEYWORDS = [
    "faith", "prayer", "sin", "grace", "suffering", "election", "holiness",
    "the cross", "the Holy Spirit", "assurance", "repentance", "the church",
    "the love of Christ", "the sovereignty of God", "the resurrection",
    "the judgment", "the gospel", "sanctification", "justification"
]


def clean_text(text: str) -> str:
    """Basic cleaning of sermon text."""
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text


def extract_chunks(text: str, max_chunks: int = 3) -> List[str]:
    """Split sermon into reasonably sized chunks."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""

    for sent in sentences:
        if len(current) + len(sent) > CHUNK_SIZE and len(current) > MIN_CHUNK_LENGTH:
            chunks.append(current.strip())
            current = sent + " "
            if len(chunks) >= max_chunks:
                break
        else:
            current += sent + " "

    if current and len(current) > MIN_CHUNK_LENGTH:
        chunks.append(current.strip())

    return chunks[:max_chunks]


def extract_topic(chunk: str) -> str:
    """Try to find a relevant topic from the chunk."""
    chunk_lower = chunk.lower()
    for topic in TOPIC_KEYWORDS:
        if topic in chunk_lower:
            return topic
    return random.choice(["faith", "grace", "the cross", "prayer", "holiness"])


def generate_grounded_answer(chunk: str, topic: str) -> str:
    """
    Create a Spurgeon-flavored answer that stays very close to the source text.
    This is the key for 'fidelity to the text'.
    """
    # Take real phrases from the chunk
    sentences = re.split(r'(?<=[.!?])\s+', chunk)
    key_sentences = sentences[:3]  # Use the first few real sentences

    # Build a response that heavily quotes/paraphrases the source
    answer = (
        f"{random.choice(['Beloved,', 'My brethren,', 'Dear friends,', ''])} "
        f"{key_sentences[0] if key_sentences else ''} "
        f"{key_sentences[1] if len(key_sentences) > 1 else ''} "
        f"This is the truth we must hold fast. "
        f"{key_sentences[2] if len(key_sentences) > 2 else ''}"
    )

    # Add a typical Spurgeon-style closing
    closings = [
        "May God grant us grace to believe and practice these things.",
        "Let us look to Jesus and rest in His finished work.",
        "This is our comfort in every trial.",
        "Oh, that we may know more of this precious truth!",
    ]
    answer += " " + random.choice(closings)

    return answer.strip()


def create_example(chunk: str) -> Dict:
    """Create one high-fidelity training example."""
    topic = extract_topic(chunk)
    question_template = random.choice(QUESTION_TEMPLATES)
    question = question_template.format(topic=topic)

    answer = generate_grounded_answer(chunk, topic)

    # Format in ChatML style (same as our previous starter)
    return {
        "messages": [
            {
                "role": "system",
                "content": "You are Charles Haddon Spurgeon. Answer using only the information in the provided CONTEXT. Stay very close to the actual text."
            },
            {
                "role": "user",
                "content": f"CONTEXT:\n{chunk}\n\nQUESTION:\n{question}"
            },
            {
                "role": "assistant",
                "content": answer
            }
        ]
    }


def main():
    print("=== Autonomous Spurgeon Dataset Generator (No API) ===")
    print(f"Looking for sermons in: {SERMONS_DIR}")

    if not SERMONS_DIR.exists():
        print("ERROR: Sermon directory not found!")
        return

    sermon_files = list(SERMONS_DIR.rglob("sermon*.md"))
    print(f"Found {len(sermon_files)} sermon files.")

    random.shuffle(sermon_files)

    examples = []
    processed = 0

    for sermon_file in tqdm(sermon_files, desc="Processing sermons"):
        if len(examples) >= MAX_EXAMPLES:
            break

        try:
            text = sermon_file.read_text(encoding="utf-8", errors="ignore")
            # Remove title/header if present
            text = re.sub(r'^#.*?\n', '', text, count=1)

            chunks = extract_chunks(text)

            for chunk in chunks:
                if len(examples) >= MAX_EXAMPLES:
                    break
                example = create_example(chunk)
                examples.append(example)

            processed += 1

        except Exception as e:
            continue

    # Save
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"\n✅ Successfully generated {len(examples)} training examples.")
    print(f"Saved to: {OUTPUT_FILE}")
    print(f"Processed {processed} sermons.")


if __name__ == "__main__":
    main()
