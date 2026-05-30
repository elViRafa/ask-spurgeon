"""
Standalone test script for Ask Spurgeon RAG pipeline.

This simulates what the Streamlit app does for sample questions,
without needing a browser. Useful for quick validation after ingestion.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from llama_index.core import Settings, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from config import (
    EMBEDDING_MODEL,
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    GROQ_API_KEY,
    PRIMARY_MODEL,
    TEMPERATURE,
    MAX_TOKENS,
)

from utils.prompts import get_system_prompt


def main():
    print("=" * 70)
    print("ASK SPURGEON — SAMPLE QUERY TEST")
    print("=" * 70)
    print()

    # 1. Setup models
    print("[1/4] Loading embedding model...")
    embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL)
    Settings.embed_model = embed_model

    print("[2/4] Connecting to Qdrant...")
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    vector_store = QdrantVectorStore(
        client=qdrant_client,
        collection_name=QDRANT_COLLECTION,
    )

    print("[3/4] Loading vector index...")
    index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)

    print("[4/4] Initializing Groq LLM...")
    llm = Groq(
        model=PRIMARY_MODEL,
        api_key=GROQ_API_KEY,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )

    print()
    print("Ready! Running sample queries...\n")

    # Sample questions (good for early sermons)
    sample_questions = [
        "What did Spurgeon teach about the immutability of God?",
        "What does Spurgeon say about suffering and reigning with Jesus?",
        "How does Spurgeon describe the relationship between God's sovereignty and human responsibility?",
    ]

    retriever = index.as_retriever(similarity_top_k=5)

    for i, question in enumerate(sample_questions, 1):
        print("=" * 70)
        print(f"QUERY {i}: {question}")
        print("=" * 70)

        # Retrieve
        nodes = retriever.retrieve(question)

        if not nodes:
            print("No relevant sources found.\n")
            continue

        # Build context
        context_blocks = []
        for node in nodes[:4]:
            meta = node.metadata or {}
            excerpt = node.get_content()[:550].strip()
            ref = f"[Sermon {meta.get('sermon_number', '?')} — \"{meta.get('title', '')}\"]"
            context_blocks.append(f"{ref}\n{excerpt}")

        context_str = "\n\n".join(context_blocks)

        # Build prompt (same style as the app)
        system = get_system_prompt()
        user_msg = (
            f"CONTEXT (excerpts from Charles Haddon Spurgeon's sermons):\n\n{context_str}\n\n"
            f"QUESTION: {question}\n\n"
            "Answer in the voice and style of Spurgeon, grounded strictly in the context above. "
            "Cite sermon numbers and titles when relevant."
        )

        from llama_index.core.llms import ChatMessage, MessageRole
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system),
            ChatMessage(role=MessageRole.USER, content=user_msg),
        ]

        # Generate
        print("Retrieving sources and generating answer with Groq...\n")
        try:
            resp = llm.chat(messages)
            answer = str(resp).strip()
            print("SPURGEON'S ANSWER:\n")
            print(answer)
        except Exception as e:
            print(f"ERROR generating answer: {e}")
            continue

        # Show sources
        print("\n\n--- TOP SOURCES USED ---")
        for j, node in enumerate(nodes[:4], 1):
            meta = node.metadata or {}
            score = getattr(node, "score", None)
            score_str = f" (score: {score:.3f})" if score else ""
            print(f"{j}. Sermon {meta.get('sermon_number', '?')} — {meta.get('title', 'Untitled')}{score_str}")
            if meta.get("primary_scripture"):
                print(f"   Primary text: {meta['primary_scripture']}")
            if meta.get("volume"):
                print(f"   Volume: {meta['volume']}")

        print("\n")

    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
