#!/usr/bin/env python3
"""
Ask Spurgeon — RAG Evaluation CLI

Convenient top-level entrypoint for evaluating the quality of the RAG system.

Usage examples:

    # Run all 20 test questions with LLM-as-Judge
    python eval.py

    # Quick test with first 5 questions
    python eval.py --limit 5

    # Compare two prompt variants with judge scoring
    python eval.py --compare default strict

    # Compare and save detailed results
    python eval.py --compare default strict --limit 10 --save comparison.json

    # Run evaluation without judge (faster)
    python eval.py --no-judge
"""

import argparse
import sys
from pathlib import Path

# Ensure we can import local modules
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

from tests.evaluate_rag import main as run_evaluation
from tests.compare_prompts import main as run_comparison


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Ask Spurgeon RAG Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python eval.py                          # Full eval with LLM judge (default)
  python eval.py --no-judge               # Run without judge (faster)
  python eval.py --limit 5                # Quick test
  python eval.py --compare default strict # Compare two prompt variants
  python eval.py --compare default concise --save results.json
        """,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of test questions to run",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=6,
        help="Number of chunks to retrieve per question (default: 6)",
    )
    parser.add_argument(
        "--judge",
        action="store_true",
        default=True,
        help="Enable LLM-as-Judge scoring (default: enabled)",
    )
    parser.add_argument(
        "--no-judge",
        dest="judge",
        action="store_false",
        help="Disable LLM-as-Judge scoring (faster, cheaper)",
    )
    parser.add_argument(
        "--save",
        type=str,
        default=None,
        help="Save full results to a JSON file",
    )

    # Comparison mode
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("VARIANT_A", "VARIANT_B"),
        default=None,
        help="Compare two prompt variants (e.g. --compare default strict)",
    )

    parser.add_argument(
        "--prompt-variant",
        default="default",
        choices=["default", "strict", "concise"],
        help="Prompt variant to use when not in comparison mode (default: default)",
    )

    args = parser.parse_args()

    if args.compare:
        # Comparison mode
        variant_a, variant_b = args.compare

        # Build argv for compare_prompts.py
        compare_argv = [
            "--variant-a", variant_a,
            "--variant-b", variant_b,
        ]
        if args.limit:
            compare_argv += ["--limit", str(args.limit)]
        if args.top_k != 6:
            compare_argv += ["--top-k", str(args.top_k)]
        if args.save:
            compare_argv += ["--save", args.save]

        # Call the comparison script
        sys.argv = ["compare_prompts.py"] + compare_argv
        run_comparison()

    else:
        # Normal evaluation mode
        eval_argv = []

        if args.limit:
            eval_argv += ["--limit", str(args.limit)]
        if args.top_k != 6:
            eval_argv += ["--top-k", str(args.top_k)]
        if args.save:
            eval_argv += ["--save", args.save]
        if args.judge:
            eval_argv += ["--judge"]
        if args.prompt_variant != "default":
            eval_argv += ["--prompt-variant", args.prompt_variant]

        sys.argv = ["evaluate_rag.py"] + eval_argv
        run_evaluation()


if __name__ == "__main__":
    main()
