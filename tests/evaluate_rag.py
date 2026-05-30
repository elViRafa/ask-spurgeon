"""
RAG Evaluation Script for "Ask Spurgeon"

Runs a set of curated theological questions through the current RAG pipeline
and produces a detailed report on retrieval quality and answer generation.

Usage:
    python tests/evaluate_rag.py
    python tests/evaluate_rag.py --limit 5                              # Run only first 5
    python tests/evaluate_rag.py --judge                                # Enable LLM-as-Judge
    python tests/evaluate_rag.py --prompt-variant strict --judge        # Test strict prompt
    python tests/evaluate_rag.py --judge --save results.json
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Make sure we can import from project root when running this script
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

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
    FALLBACK_MODEL,   # Use the faster 8B model for judging
    TEMPERATURE,
    MAX_TOKENS,
)

from utils.prompts import get_system_prompt, build_judge_prompt
from tests.rag_test_questions import get_all_test_questions, RAGTestQuestion


def setup_models(use_judge: bool = False):
    """Initialize embedding model and LLM (same as the main app)."""
    print("Loading embedding model...")
    embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL)
    Settings.embed_model = embed_model

    print("Connecting to Qdrant...")
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    vector_store = QdrantVectorStore(
        client=qdrant_client,
        collection_name=QDRANT_COLLECTION,
    )

    print("Loading vector index...")
    index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)

    print("Initializing Groq LLM (generator)...")
    llm = Groq(
        model=PRIMARY_MODEL,
        api_key=GROQ_API_KEY,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )

    judge_llm = None
    if use_judge:
        print("Initializing Groq LLM (judge - using faster 8B model)...")
        judge_llm = Groq(
            model=FALLBACK_MODEL,   # Cheaper and faster for evaluation
            api_key=GROQ_API_KEY,
            temperature=0.1,        # Low temperature for consistent judging
            max_tokens=800,
        )

    return index, llm, judge_llm


def generate_answer(question: str, nodes: List, llm: Groq, prompt_variant: str = "default") -> str:
    """Generate a Spurgeon-style answer using the same prompt pattern as the app."""
    from llama_index.core.llms import ChatMessage, MessageRole

    context_blocks = []
    for node in nodes[:5]:
        meta = node.metadata or {}
        excerpt = node.get_content()[:650].strip()
        ref = f"[Sermon {meta.get('sermon_number', '?')} — \"{meta.get('title', '')}\""
        if meta.get("volume"):
            ref += f", Vol. {meta['volume']}"
        if meta.get("primary_scripture"):
            ref += f" | {meta['primary_scripture']}"
        ref += "]"
        context_blocks.append(f"{ref}\n{excerpt}")

    context_str = "\n\n".join(context_blocks)

    system = get_system_prompt(variant=prompt_variant)
    user_msg = (
        f"CONTEXT (excerpts from Charles Haddon Spurgeon's sermons):\n\n{context_str}\n\n"
        f"QUESTION: {question}\n\n"
        "Answer in the voice and style of Spurgeon, grounded strictly in the context above. "
        "Cite specific sermon numbers and titles when possible. "
        "If the context does not contain the answer, say so plainly."
    )

    messages = [
        ChatMessage(role=MessageRole.SYSTEM, content=system),
        ChatMessage(role=MessageRole.USER, content=user_msg),
    ]

    resp = llm.chat(messages)
    return str(resp).strip()


def evaluate_question(
    q: RAGTestQuestion,
    index: VectorStoreIndex,
    llm: Groq,
    top_k: int = 6,
    prompt_variant: str = "default",
) -> Dict[str, Any]:
    """Run one test question and collect detailed results."""
    print(f"\n{'='*70}")
    print(f"[{q.id}] {q.category}")
    print(f"Q: {q.question}")
    print(f"{'='*70}")

    retriever = index.as_retriever(similarity_top_k=top_k)

    start = time.time()
    nodes = retriever.retrieve(q.question)
    retrieval_time = time.time() - start

    # Generate answer using the specified prompt variant
    start = time.time()
    answer = generate_answer(q.question, nodes, llm, prompt_variant=prompt_variant)
    generation_time = time.time() - start

    # Collect source info
    sources = []
    for node in nodes:
        meta = node.metadata or {}
        sources.append({
            "sermon_number": meta.get("sermon_number"),
            "title": meta.get("title"),
            "volume": meta.get("volume"),
            "primary_scripture": meta.get("primary_scripture"),
            "score": getattr(node, "score", None),
            "excerpt_preview": node.get_content()[:200] + "...",
        })

    result = {
        "id": q.id,
        "question": q.question,
        "category": q.category,
        "expected_themes": q.expected_themes,
        "retrieved_sources": sources,
        "generated_answer": answer,
        "retrieval_time_sec": round(retrieval_time, 2),
        "generation_time_sec": round(generation_time, 2),
        "total_time_sec": round(retrieval_time + generation_time, 2),
        "notes": q.notes,
    }

    # Simple heuristic checks
    result["heuristics"] = {
        "retrieved_anything": len(sources) > 0,
        "has_citations": "Sermon" in answer and any(str(s["sermon_number"]) in answer for s in sources if s["sermon_number"]),
        "admits_limitation": "do not find" in answer.lower() or "not addressed" in answer.lower() or "insufficient" in answer.lower(),
    }

    print(f"\nTop sources:")
    for i, s in enumerate(sources[:4], 1):
        print(f"  {i}. Sermon {s['sermon_number']} — {s['title']} (score: {s['score']:.3f})")

    print(f"\nAnswer (first 400 chars):\n{answer[:400]}...\n")

    return result


def judge_rag_output(question: str, nodes: list, answer: str, judge_llm: Groq) -> Dict[str, Any]:
    """
    Use an LLM as a judge to score the RAG output on multiple dimensions.
    Returns scores + reasoning.
    """
    from llama_index.core.llms import ChatMessage, MessageRole

    context_str = "\n\n".join(
        f"[Sermon {n.metadata.get('sermon_number', '?')} — {n.metadata.get('title', '')}]\n{n.get_content()[:500]}"
        for n in nodes[:5]
    )

    prompt = build_judge_prompt(question, context_str, answer)

    messages = [
        ChatMessage(role=MessageRole.USER, content=prompt)
    ]

    try:
        resp = judge_llm.chat(messages)
        raw = str(resp).strip()

        # Try to extract JSON from the response (LLMs sometimes wrap it in markdown)
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        scores = json.loads(raw)
        return scores
    except Exception as e:
        return {
            "error": str(e),
            "groundedness": None,
            "citation_quality": None,
            "honesty": None,
            "helpfulness": None,
            "overall_score": None,
            "reasoning": "Judge failed to produce valid output."
        }


def main():
    parser = argparse.ArgumentParser(description="Evaluate Ask Spurgeon RAG system")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of questions to run")
    parser.add_argument("--save", type=str, default=None, help="Save full results to JSON file")
    parser.add_argument("--top-k", type=int, default=6, help="Number of chunks to retrieve")
    parser.add_argument("--judge", action="store_true", help="Enable LLM-as-judge scoring (uses faster 8B model)")
    parser.add_argument("--prompt-variant", default="default", help="Prompt variant to use (default, strict, concise)")
    args = parser.parse_args()

    load_dotenv()

    questions = get_all_test_questions()
    if args.limit:
        questions = questions[:args.limit]

    print(f"\n{'='*70}")
    print("ASK SPURGEON — RAG EVALUATION SUITE")
    print(f"{'='*70}")
    print(f"Running {len(questions)} test questions against current index...")
    if args.judge:
        print("LLM-as-Judge scoring: ENABLED")
    print()

    index, llm, judge_llm = setup_models(use_judge=args.judge)

    results = []
    for q in questions:
        res = evaluate_question(q, index, llm, top_k=args.top_k, prompt_variant=args.prompt_variant)

        # Optional LLM-as-Judge scoring
        if args.judge and judge_llm:
            print("  → Running LLM judge...")
            # Re-retrieve top nodes for context (cheap operation)
            judge_nodes = index.as_retriever(similarity_top_k=5).retrieve(q.question)
            judge_result = judge_rag_output(q.question, judge_nodes, res["generated_answer"], judge_llm)
            res["llm_judge"] = judge_result

        results.append(res)

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")

    total = len(results)
    retrieved = sum(1 for r in results if r["heuristics"]["retrieved_anything"])
    cited = sum(1 for r in results if r["heuristics"]["has_citations"])
    honest = sum(1 for r in results if r["heuristics"]["admits_limitation"])

    print(f"Questions evaluated: {total}")
    print(f"Retrieved at least one source: {retrieved}/{total} ({retrieved/total*100:.1f}%)")
    print(f"Generated answers with citations: {cited}/{total} ({cited/total*100:.1f}%)")
    print(f"Properly admitted limitations (when appropriate): {honest}/{total}")

    avg_time = sum(r["total_time_sec"] for r in results) / total
    print(f"Average time per question: {avg_time:.2f}s")

    # LLM Judge Summary (if enabled)
    if any("llm_judge" in r and r["llm_judge"].get("overall_score") for r in results):
        judge_scores = [r["llm_judge"]["overall_score"] for r in results if r.get("llm_judge") and r["llm_judge"].get("overall_score")]
        if judge_scores:
            print(f"\nLLM Judge Average Overall Score: {sum(judge_scores)/len(judge_scores):.2f}/5.0")
            for dim in ["groundedness", "citation_quality", "honesty", "helpfulness"]:
                scores = [r["llm_judge"][dim] for r in results if r.get("llm_judge") and r["llm_judge"].get(dim)]
                if scores:
                    print(f"  - {dim.title():<18}: {sum(scores)/len(scores):.2f}/5.0")

    if args.save:
        output = {
            "timestamp": datetime.now().isoformat(),
            "collection": os.getenv("QDRANT_COLLECTION"),
            "generator_model": PRIMARY_MODEL,
            "judge_model": FALLBACK_MODEL if args.judge else None,
            "total_questions": total,
            "llm_judge_enabled": args.judge,
            "results": results,
        }
        Path(args.save).parent.mkdir(parents=True, exist_ok=True)
        with open(args.save, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\nFull results saved to: {args.save}")

    print("\nEvaluation complete.")


if __name__ == "__main__":
    main()
