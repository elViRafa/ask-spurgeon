"""
Prompt Comparison Tool for Ask Spurgeon RAG

Runs the same set of test questions against two different prompt variants
and compares the LLM Judge scores side-by-side.

Usage examples:
    python tests/compare_prompts.py --variant-a default --variant-b strict
    python tests/compare_prompts.py --variant-a default --variant-b concise --limit 8
    python tests/compare_prompts.py --variant-a strict --variant-b concise --save comparison.json
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv

from tests.evaluate_rag import (
    setup_models,
    evaluate_question,
    judge_rag_output,
)
from tests.rag_test_questions import get_all_test_questions
from utils.prompts import get_system_prompt


def run_evaluation_with_variant(variant: str, questions: List, top_k: int, use_judge: bool):
    """Run evaluation using a specific prompt variant."""
    print(f"\n{'='*70}")
    print(f"Running evaluation with prompt variant: '{variant}'")
    print(f"{'='*70}")

    index, llm, judge_llm = setup_models(use_judge=use_judge)

    # Temporarily patch the system prompt function for this run
    original_get = get_system_prompt.__wrapped__ if hasattr(get_system_prompt, "__wrapped__") else get_system_prompt

    results = []
    for q in questions:
        res = evaluate_question(q, index, llm, top_k=top_k, prompt_variant=variant)

        if use_judge and judge_llm:
            print(f"  [Judge] Scoring variant '{variant}'...")
            judge_nodes = index.as_retriever(similarity_top_k=5).retrieve(q.question)
            judge_result = judge_rag_output(q.question, judge_nodes, res["generated_answer"], judge_llm)
            res["llm_judge"] = judge_result

        results.append(res)

    return results


def compare_results(variant_a: str, results_a: List[Dict], variant_b: str, results_b: List[Dict]):
    """Print a side-by-side comparison of two result sets."""
    print(f"\n{'='*70}")
    print(f"PROMPT COMPARISON: '{variant_a}' vs '{variant_b}'")
    print(f"{'='*70}\n")

    print(f"{'ID':<4} {'Question (truncated)':<45} {variant_a:<10} {variant_b:<10} {'Delta':<8} Winner")
    print("-" * 90)

    total_delta = 0.0
    wins_a = 0
    wins_b = 0
    ties = 0

    for i, (ra, rb) in enumerate(zip(results_a, results_b)):
        score_a = ra.get("llm_judge", {}).get("overall_score")
        score_b = rb.get("llm_judge", {}).get("overall_score")

        q_short = ra["question"][:42] + "..." if len(ra["question"]) > 45 else ra["question"]

        if score_a is None or score_b is None:
            delta_str = "N/A"
            winner = "N/A"
        else:
            delta = score_b - score_a
            total_delta += delta
            delta_str = f"{delta:+.2f}"

            if abs(delta) < 0.1:
                winner = "Tie"
                ties += 1
            elif delta > 0:
                winner = variant_b
                wins_b += 1
            else:
                winner = variant_a
                wins_a += 1

        print(f"{ra['id']:<4} {q_short:<45} {str(score_a):<10} {str(score_b):<10} {delta_str:<8} {winner}")

    print("-" * 90)

    if wins_a + wins_b + ties > 0:
        print(f"\nSummary:")
        print(f"  {variant_a} wins: {wins_a}")
        print(f"  {variant_b} wins: {wins_b}")
        print(f"  Ties:           {ties}")
        print(f"  Average delta (B - A): {total_delta / (wins_a + wins_b + ties):+.3f}")

    # Per-category breakdown
    print(f"\nPer-Category Average Overall Score:")
    categories = {}
    for ra, rb in zip(results_a, results_b):
        cat = ra["category"]
        if cat not in categories:
            categories[cat] = {"a": [], "b": []}
        if ra.get("llm_judge"):
            categories[cat]["a"].append(ra["llm_judge"].get("overall_score"))
        if rb.get("llm_judge"):
            categories[cat]["b"].append(rb["llm_judge"].get("overall_score"))

    for cat, scores in categories.items():
        avg_a = sum(s for s in scores["a"] if s) / len([s for s in scores["a"] if s]) if scores["a"] else 0
        avg_b = sum(s for s in scores["b"] if s) / len([s for s in scores["b"] if s]) if scores["b"] else 0
        print(f"  {cat:<30} {variant_a}: {avg_a:.2f}   {variant_b}: {avg_b:.2f}   Δ {avg_b - avg_a:+.2f}")


def main():
    parser = argparse.ArgumentParser(description="Compare two prompt variants using LLM Judge")
    parser.add_argument("--variant-a", required=True, help="First prompt variant (e.g. default, strict, concise)")
    parser.add_argument("--variant-b", required=True, help="Second prompt variant")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of questions")
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument("--save", type=str, default=None, help="Save detailed comparison to JSON")
    args = parser.parse_args()

    load_dotenv()

    questions = get_all_test_questions()
    if args.limit:
        questions = questions[:args.limit]

    results_a = run_evaluation_with_variant(args.variant_a, questions, args.top_k, use_judge=True)
    results_b = run_evaluation_with_variant(args.variant_b, questions, args.top_k, use_judge=True)

    compare_results(args.variant_a, results_a, args.variant_b, results_b)

    if args.save:
        output = {
            "timestamp": datetime.now().isoformat(),
            "variant_a": args.variant_a,
            "variant_b": args.variant_b,
            "results_a": results_a,
            "results_b": results_b,
        }
        Path(args.save).parent.mkdir(parents=True, exist_ok=True)
        with open(args.save, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\nDetailed comparison saved to: {args.save}")


if __name__ == "__main__":
    main()
