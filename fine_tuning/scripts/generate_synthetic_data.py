#!/usr/bin/env python3
"""
Synthetic Data Generator for Spurgeon Fine-Tuning (High Fidelity Version)

This script generates training data where:
- Context is retrieved from the existing vector database.
- A strong teacher model (Groq) generates answers STRICTLY based on that context.
- Answers are phrased in Spurgeon's voice.

The goal is maximum faithfulness to the source text.

Usage:
    python fine_tuning/scripts/generate_synthetic_data.py --limit 2000 --output fine_tuning/data/spurgeon_synthetic.jsonl
"""

import os
import json
import argparse
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

# Groq client
try:
    from groq import Groq
except ImportError:
    print("Please install groq: pip install groq")
    exit(1)

# Project imports
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from config import (
    VECTOR_STORE, CHROMA_PERSIST_DIR, CHROMA_COLLECTION,
    CHROMA_HOST, CHROMA_PORT
)
from utils.bible_refs import extract_bible_references

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


def get_vector_store():
    """Get the vector store based on current project config."""
    if VECTOR_STORE == "chroma":
        import chromadb
        from llama_index.vector_stores.chroma import ChromaVectorStore
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        from llama_index.core import VectorStoreIndex, Settings

        Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

        if CHROMA_PERSIST_DIR:
            client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        else:
            client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

        collection = client.get_or_create_collection(CHROMA_COLLECTION)
        vector_store = ChromaVectorStore(chroma_collection=collection)
        index = VectorStoreIndex.from_vector_store(vector_store)
        return index.as_retriever(similarity_top_k=5)
    else:
        raise NotImplementedError("Qdrant version not yet implemented in this script. Use Chroma for now.")


def generate_spurgeon_response(question: str, context: str, groq_client: Groq) -> str:
    """Call the teacher model with strict fidelity instructions."""
    prompt = TEACHER_PROMPT.format(context=context, question=question)

    try:
        response = groq_client.chat.completions.create(
            model=TEACHER_MODEL,
            messages=[
                {"role": "system", "content": "You are a careful theological writer who only uses the provided source material."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1200,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating response: {e}")
        return ""


def format_chatml_example(question: str, context: str, answer: str) -> Dict:
    """Format as Llama-3 ChatML for fine-tuning."""
    return {
        "messages": [
            {
                "role": "system",
                "content": "You are Charles Haddon Spurgeon. Answer the user's question using only the provided sermon excerpts. Speak in your authentic 19th-century voice."
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
    parser.add_argument("--output", type=str, default="fine_tuning/data/spurgeon_synthetic.jsonl")
    parser.add_argument("--questions-file", type=str, default=None, help="Optional file with questions (one per line)")
    args = parser.parse_args()

    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not found in environment.")
        return

    groq_client = Groq(api_key=GROQ_API_KEY)
    retriever = get_vector_store()

    # Load or generate questions
    if args.questions_file and Path(args.questions_file).exists():
        with open(args.questions_file, "r", encoding="utf-8") as f:
            questions = [line.strip() for line in f if line.strip()][:args.limit]
    else:
        # Default set of good questions for Spurgeon style
        questions = [
            "What did Spurgeon teach about the sovereignty of God in suffering?",
            "How does Spurgeon explain the relationship between faith and works?",
            "What counsel does Spurgeon give to those struggling with assurance?",
            "How does Spurgeon preach on the doctrine of election?",
            "What does Spurgeon say about the role of the Holy Spirit in the believer's life?",
            # Add more good questions here...
        ] * (args.limit // 5 + 1)
        questions = questions[:args.limit]

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating {len(questions)} synthetic examples with high fidelity...")

    with open(output_path, "w", encoding="utf-8") as f:
        for question in tqdm(questions):
            # Retrieve context using existing RAG
            nodes = retriever.retrieve(question)
            context = "\n\n".join([node.get_content() for node in nodes])

            if not context.strip():
                continue

            # Generate high-fidelity Spurgeon-style answer
            answer = generate_spurgeon_response(question, context, groq_client)

            if not answer or len(answer) < 50:
                continue

            # Format and save
            example = format_chatml_example(question, context, answer)
            f.write(json.dumps(example, ensure_ascii=False) + "\n")

    print(f"\nDone! Saved {len(questions)} examples to {output_path}")


if __name__ == "__main__":
    main()
