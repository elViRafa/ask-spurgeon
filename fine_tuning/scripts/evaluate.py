#!/usr/bin/env python3
"""Reproducible post-SFT evaluation against the frozen fixed-context set.

Backends:
  ollama:<model>   local Ollama /api/chat
  hf:<path-or-id>  Transformers AutoModelForCausalLM
  openai:<model>   CUSTOM_LLM_BASE_URL OpenAI-compatible endpoint

Examples:
  python fine_tuning/scripts/evaluate.py --candidate ollama:spurgeon-qa-v2
  python fine_tuning/scripts/evaluate.py --candidate hf:./merged-sft --baseline hf:./merged-cpt --judge
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

REPO = Path(__file__).resolve().parent.parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
for search_path in (REPO, SCRIPT_DIR):
    if str(search_path) not in sys.path:
        sys.path.insert(0, str(search_path))
load_dotenv(REPO / ".env")

from config import (  # noqa: E402
    CUSTOM_LLM_API_KEY,
    CUSTOM_LLM_BASE_URL,
    SFT_EVAL_JUDGE_API_KEY,
    SFT_EVAL_JUDGE_BASE_URL,
    SFT_EVAL_JUDGE_MODEL,
    SFT_EVAL_JUDGE_PROVIDER,
    SFT_EVAL_JUDGE_TIMEOUT,
)
from sft_eval_core import (  # noqa: E402
    REPORT_SCHEMA_VERSION,
    aggregate_pairwise_judgments,
    analyze_output,
    context_of,
    load_jsonl,
    pairwise_judge_prompt,
    parse_judge_json,
    release_gates,
    refresh_report_metrics,
    sha256_file,
    summarize_records,
    validate_report,
)
from sft_stop_token_utils import apply_sft_special_token_contract  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Cannot reach {url}: {exc}") from exc


def append_jsonl(path: Path | None, payload: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        handle.flush()


class OllamaBackend:
    def __init__(self, model: str, host: str, timeout: int, num_ctx: int):
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout
        self.num_ctx = num_ctx

    def identity(self) -> dict[str, Any]:
        shown = post_json(
            f"{self.host}/api/show", {"model": self.model}, {}, self.timeout
        )
        stable = {
            "template": shown.get("template"),
            "parameters": shown.get("parameters"),
            "model_info": shown.get("model_info"),
            "details": shown.get("details"),
        }
        canonical = json.dumps(stable, sort_keys=True, ensure_ascii=False, default=str)
        return {
            "model": self.model,
            "config_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "details": shown.get("details"),
        }

    def generate(self, messages: list[dict[str, str]], max_tokens: int) -> dict[str, Any]:
        prompt = "".join(
            f"<|im_start|>{message['role']}\n{message['content']}<|im_end|>\n"
            for message in messages
        )
        prompt += "<|im_start|>assistant\n"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "raw": True,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": max_tokens,
                "num_ctx": self.num_ctx,
                "seed": 3407,
                # Use only the contractual turn stop. Stopping on im_start would
                # strip and conceal a leaked user/system turn.
                "stop": ["<|im_end|>"],
            },
        }
        result = post_json(f"{self.host}/api/generate", payload, {}, self.timeout)
        text = result.get("response", "")
        return {
            "text": text,
            "raw_text": text,
            "api_stop": result.get("done_reason") == "stop",
            "metadata": {
                "done_reason": result.get("done_reason"),
                "prompt_eval_count": result.get("prompt_eval_count"),
                "eval_count": result.get("eval_count"),
            },
        }


class OpenAIBackend:
    def __init__(self, model: str, base_url: str, api_key: str, timeout: int):
        if not base_url:
            raise ValueError("CUSTOM_LLM_BASE_URL is required for an openai: backend")
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def identity(self) -> dict[str, Any]:
        return {"model": self.model, "base_url": self.base_url}

    def generate(self, messages: list[dict[str, str]], max_tokens: int) -> dict[str, Any]:
        result = post_json(
            f"{self.base_url}/chat/completions",
            {
                "model": self.model,
                "messages": messages,
                "temperature": 0.0,
                "max_tokens": max_tokens,
                "seed": 3407,
            },
            {"Authorization": f"Bearer {self.api_key}"},
            self.timeout,
        )
        choice = result["choices"][0]
        text = choice["message"]["content"]
        return {
            "text": text,
            "raw_text": text,
            "api_stop": choice.get("finish_reason") == "stop",
            "metadata": {"finish_reason": choice.get("finish_reason"), "usage": result.get("usage")},
        }


class HFBackend:
    def __init__(self, model_name: str, max_seq_length: int):
        import torch
        from transformers import AutoModelForCausalLM

        from sft_stop_token_utils import load_qwen35_tokenizer

        self.model_name = model_name
        self.torch = torch
        self.tokenizer, self.im_end_id, self.eot_id = apply_sft_special_token_contract(
            load_qwen35_tokenizer(model_name)
        )
        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=dtype,
            device_map="auto" if torch.cuda.is_available() else None,
            trust_remote_code=True,
        )
        if not torch.cuda.is_available():
            self.model.to("cpu")
        self.model.eval()
        self.max_seq_length = max_seq_length

    def identity(self) -> dict[str, Any]:
        return {
            "model": self.model_name,
            "config_sha256": hashlib.sha256(
                self.model.config.to_json_string().encode("utf-8")
            ).hexdigest(),
        }

    def generate(self, messages: list[dict[str, str]], max_tokens: int) -> dict[str, Any]:
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_seq_length,
        )
        device = next(self.model.parameters()).device
        inputs = {key: value.to(device) for key, value in inputs.items()}
        with self.torch.inference_mode():
            output = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=False,
                eos_token_id=[self.im_end_id, self.eot_id],
                pad_token_id=self.tokenizer.pad_token_id,
            )
        token_ids = output[0][inputs["input_ids"].shape[1] :].tolist()
        raw = self.tokenizer.decode(token_ids, skip_special_tokens=False)
        text = raw.split("<|im_end|>")[0].strip()
        return {
            "text": text,
            "raw_text": raw,
            "raw_token_ids": token_ids,
            "im_end_id": self.im_end_id,
            "eot_id": self.eot_id,
            "api_stop": False,
            "metadata": {},
        }


def make_backend(spec: str, args: argparse.Namespace):
    if ":" not in spec:
        raise ValueError(f"Backend must be prefixed with ollama:, hf:, or openai:: {spec}")
    kind, model = spec.split(":", 1)
    if not model:
        raise ValueError(f"Missing model in backend specification: {spec}")
    if kind == "ollama":
        return OllamaBackend(model, args.ollama_host, args.timeout, args.max_seq_length)
    if kind == "hf":
        return HFBackend(model, args.max_seq_length)
    if kind == "openai":
        return OpenAIBackend(
            model, CUSTOM_LLM_BASE_URL, CUSTOM_LLM_API_KEY, args.timeout
        )
    raise ValueError(f"Unsupported backend {kind!r}")


class JudgeClient:
    def __init__(self, *, model: str, base_url: str, api_key: str, timeout: int, retries: int):
        if not api_key:
            raise ValueError(
                "Semantic judging requires SFT_EVAL_JUDGE_API_KEY or GROQ_API_KEY in .env"
            )
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.retries = retries

    def _chat(self, prompt: str) -> tuple[str, str | None]:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                result = post_json(
                    f"{self.base_url}/chat/completions",
                    {
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.0,
                        "max_tokens": 6000,
                        "response_format": {"type": "json_object"},
                    },
                    {"Authorization": f"Bearer {self.api_key}"},
                    self.timeout,
                )
                return result["choices"][0]["message"]["content"], result.get("model")
            except (KeyError, IndexError, TypeError, ValueError, RuntimeError) as exc:
                last_error = exc
                if attempt < self.retries:
                    delay = min(15 * (2**attempt), 120) if "HTTP 429" in str(exc) else min(2**attempt, 5)
                    time.sleep(delay)
        raise RuntimeError(f"Judge failed after {self.retries + 1} attempts: {last_error}")

    def score(self, prompt: str) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            text, served_model = self._chat(prompt)
            try:
                parsed = parse_judge_json(text)
                parsed["_served_model"] = served_model
                return parsed
            except (json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(min(2**attempt, 5))
        raise RuntimeError(f"Judge returned malformed JSON: {last_error}")

    def score_batch(self, prompt: str, expected_ids: list[str]) -> list[dict[str, Any]]:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            text, served_model = self._chat(prompt)
            try:
                stripped = text.strip()
                if stripped.startswith("```"):
                    stripped = (
                        stripped.removeprefix("```json")
                        .removeprefix("```")
                        .removesuffix("```")
                        .strip()
                    )
                start, finish = stripped.find("{"), stripped.rfind("}")
                if start < 0 or finish < start:
                    raise ValueError("batch judge response does not contain JSON")
                payload = json.loads(stripped[start : finish + 1])
                rows = payload.get("judgments")
                if not isinstance(rows, list):
                    raise ValueError("batch judge response missing judgments list")
                by_id = {str(row.get("id")): row for row in rows if isinstance(row, dict)}
                if set(by_id) != set(expected_ids):
                    raise ValueError(
                        f"batch judge IDs mismatch: expected {expected_ids}, got {sorted(by_id)}"
                    )
                parsed_rows = []
                for item_id in expected_ids:
                    row = parse_judge_json(json.dumps(by_id[item_id]))
                    row["_served_model"] = served_model
                    parsed_rows.append(row)
                return parsed_rows
            except (json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(min(2**attempt, 5))
        raise RuntimeError(f"Batch judge returned malformed JSON: {last_error}")

def run_model(
    backend: Any,
    items: list[dict[str, Any]],
    *,
    model_spec: str,
    max_tokens: int,
    progress_path: Path | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        started = time.perf_counter()
        generated = backend.generate(item["messages"][:-1], max_tokens)
        latency = round(time.perf_counter() - started, 4)
        record = analyze_output(
                index,
                item["messages"],
                generated["text"],
                raw_text=generated.get("raw_text"),
                raw_token_ids=generated.get("raw_token_ids"),
                im_end_id=generated.get("im_end_id"),
                eot_id=generated.get("eot_id"),
                api_stop=generated.get("api_stop", False),
                latency_seconds=latency,
                backend_metadata=generated.get("metadata"),
            )
        records.append(record)
        append_jsonl(progress_path, record)
        print(f"{model_spec}: {index + 1}/{len(items)}", flush=True)
    return records, summarize_records(records)


def run_judge(
    client: JudgeClient,
    candidate: list[dict[str, Any]],
    baseline: list[dict[str, Any]],
    *,
    orders: int,
    progress_path: Path | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    judgments: list[dict[str, Any]] = []
    for index, (candidate_row, baseline_row) in enumerate(zip(candidate, baseline, strict=True)):
        for order in range(orders):
            candidate_side = "A" if order % 2 == 0 else "B"
            answer_a = (
                candidate_row["prediction"]
                if candidate_side == "A"
                else baseline_row["prediction"]
            )
            answer_b = (
                baseline_row["prediction"]
                if candidate_side == "A"
                else candidate_row["prediction"]
            )
            result = client.score(
                pairwise_judge_prompt(
                    question=candidate_row["question"],
                    context=context_of(candidate_row["user"]),
                    answer_a=answer_a,
                    answer_b=answer_b,
                )
            )
            judgment = {
                "index": index,
                "example_id": candidate_row["example_id"],
                "candidate_side": candidate_side,
                "result": result,
            }
            judgments.append(judgment)
            append_jsonl(progress_path, judgment)
        print(f"judge: {index + 1}/{len(candidate)}", flush=True)
    return judgments, aggregate_pairwise_judgments(judgments)


def batch_judge_prompt(items: list[dict[str, str]]) -> str:
    blocks = []
    for item in items:
        blocks.append(
            f"""ID: {item['id']}
QUESTION:
{item['question']}

CONTEXT:
{item['context']}

ANSWER A:
{item['answer_a']}

ANSWER B:
{item['answer_b']}
"""
        )
    return """You are an independent evaluator of grounded theological question answering.

For every ID, score Answer A and Answer B from 1 to 5 on groundedness,
correctness, citation_quality, honesty, and style. Choose winner A, B, or tie.
Ignore answer order and verbosity. Unsupported polished claims must score poorly.
Style means clear knowledge-assistant prose without preacher roleplay or reader vocatives.

Output only one JSON object:
{"judgments": [
  {"id": "given-id", "A": {"groundedness": 1, "correctness": 1, "citation_quality": 1, "honesty": 1, "style": 1}, "B": {"groundedness": 1, "correctness": 1, "citation_quality": 1, "honesty": 1, "style": 1}, "winner": "A", "reasoning": "brief evidence-based reason"}
]}

Return exactly one judgment for every supplied ID.

""" + "\n---\n".join(blocks)


def run_judge_batched(
    client: JudgeClient,
    candidate: list[dict[str, Any]],
    baseline: list[dict[str, Any]],
    *,
    orders: int,
    batch_size: int,
    progress_path: Path | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    judgments: list[dict[str, Any]] = []
    if progress_path and progress_path.is_file():
        with progress_path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    judgments.append(json.loads(line))
    completed = {
        (row["example_id"], row["candidate_side"]) for row in judgments
    }
    pending: list[dict[str, Any]] = []
    for index, (candidate_row, baseline_row) in enumerate(zip(candidate, baseline, strict=True)):
        for order in range(orders):
            candidate_side = "A" if order % 2 == 0 else "B"
            if (candidate_row["example_id"], candidate_side) in completed:
                continue
            pending.append(
                {
                    "id": f"{candidate_row['example_id']}:{order}",
                    "index": index,
                    "example_id": candidate_row["example_id"],
                    "candidate_side": candidate_side,
                    "question": candidate_row["question"],
                    "context": context_of(candidate_row["user"]),
                    "answer_a": (
                        candidate_row["prediction"]
                        if candidate_side == "A"
                        else baseline_row["prediction"]
                    ),
                    "answer_b": (
                        baseline_row["prediction"]
                        if candidate_side == "A"
                        else candidate_row["prediction"]
                    ),
                }
            )

    batches = [pending[start : start + batch_size] for start in range(0, len(pending), batch_size)]
    for batch_index, batch in enumerate(batches, 1):
        results = client.score_batch(
            batch_judge_prompt(batch), [item["id"] for item in batch]
        )
        for item, result in zip(batch, results, strict=True):
            judgment = {
                "index": item["index"],
                "example_id": item["example_id"],
                "candidate_side": item["candidate_side"],
                "result": result,
            }
            judgments.append(judgment)
            append_jsonl(progress_path, judgment)
        print(
            f"judge batch: {batch_index}/{len(batches)} "
            f"({len(judgments)}/{len(candidate) * orders} judgments)",
            flush=True,
        )
    return judgments, aggregate_pairwise_judgments(judgments)


def artifact_fingerprint(path_text: str) -> dict[str, Any] | None:
    if not path_text:
        return None
    path = Path(path_text).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Artifact does not exist: {path}")
    if path.is_file():
        return {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
    files: list[dict[str, Any]] = []
    for match in sorted(item for item in path.rglob("*") if item.is_file()):
        relative = match.relative_to(path).as_posix()
        if relative.startswith(".cache/"):
            continue
        files.append(
            {
                "path": relative,
                "bytes": match.stat().st_size,
                "sha256": sha256_file(match),
            }
        )
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":"))
    return {
        "path": str(path),
        "file_count": len(files),
        "bytes": sum(item["bytes"] for item in files),
        "manifest_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "files": files,
    }


def write_human_review(path: Path, report: dict[str, Any], sample_size: int, seed: int) -> None:
    candidate = report["candidate"]["records"]
    baseline = (report.get("baseline") or {}).get("records") or []
    judgments = (report.get("judge") or {}).get("judgments") or []
    judge_by_id: dict[str, list[dict[str, Any]]] = {}
    semantic_failures: set[str] = set()
    for judgment in judgments:
        judge_by_id.setdefault(judgment["example_id"], []).append(judgment)
        candidate_side = judgment["candidate_side"]
        scores = judgment["result"][candidate_side]
        if scores["groundedness"] < 4 or scores["correctness"] < 4:
            semantic_failures.add(judgment["example_id"])
    failed = [
        row for row in candidate if row["failures"] or row["example_id"] in semantic_failures
    ]
    failed_ids = {row["example_id"] for row in failed}
    passed = [row for row in candidate if row["example_id"] not in failed_ids]
    rng = random.Random(seed)
    selected = failed + rng.sample(passed, min(sample_size, len(passed)))
    baseline_by_id = {row["example_id"]: row for row in baseline}
    lines = [
        "# Post-SFT human review",
        "",
        f"Generated: {report['created_at']}",
        f"Dataset SHA-256: `{report['dataset']['sha256']}`",
        f"Release gates: **{'PASS' if report['gates']['pass'] else 'FAIL'}**",
        "",
    ]
    for row in selected:
        lines.extend(
            [
                f"## {row['index']}: {row['example_id']} ({row['slice']})",
                f"Failures: {', '.join(row['failures']) or 'seeded pass'}",
                "",
                f"Question: {row['question']}",
                "",
                "Candidate:",
                row["prediction"],
                "",
            ]
        )
        baseline_row = baseline_by_id.get(row["example_id"])
        if baseline_row:
            lines.extend(["Baseline:", baseline_row["prediction"], ""])
        for judgment in judge_by_id.get(row["example_id"], []):
            side = judgment["candidate_side"]
            lines.extend(
                [
                    f"Judge ({side}=candidate): {json.dumps(judgment['result'][side])}",
                    f"Reason: {judgment['result']['reasoning']}",
                    "",
                ]
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Post-SFT frozen-set evaluation")
    parser.add_argument("--candidate", default="ollama:spurgeon-qa-v2")
    parser.add_argument("--baseline", default="none")
    parser.add_argument(
        "--test-set",
        default=str(REPO / "fine_tuning" / "data" / "qa_test_frozen.jsonl"),
    )
    parser.add_argument(
        "--output",
        default=str(REPO / "fine_tuning" / "eval_results" / "post_sft_eval.json"),
    )
    parser.add_argument("--candidate-artifact", default="")
    parser.add_argument(
        "--source-adapter-artifact",
        default="",
        help="Optional LoRA adapter file used to produce the evaluated candidate",
    )
    parser.add_argument("--baseline-artifact", default="")
    parser.add_argument("--ollama-host", default="http://localhost:11434")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--max-tokens", type=int, default=400)
    parser.add_argument("--max-seq-length", type=int, default=4096)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--judge", action="store_true")
    parser.add_argument("--judge-orders", type=int, choices=(1, 2), default=2)
    parser.add_argument("--judge-batch-size", type=int, default=5)
    parser.add_argument("--judge-retries", type=int, default=2)
    parser.add_argument(
        "--judge-existing-report",
        default="",
        help="Skip generation and add judging to an existing deterministic report",
    )
    parser.add_argument(
        "--refresh-existing-report",
        default="",
        help="Recompute deterministic metrics from an existing report without generation",
    )
    parser.add_argument("--review-sample", type=int, default=10)
    parser.add_argument("--seed", type=int, default=3407)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.limit < 0:
        raise ValueError("--limit must be non-negative")
    if args.judge_batch_size < 1:
        raise ValueError("--judge-batch-size must be positive")
    if args.refresh_existing_report:
        output = Path(args.refresh_existing_report).resolve()
        report = json.loads(output.read_text(encoding="utf-8"))
        refresh_report_metrics(report)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        review_path = output.with_name(f"{output.stem}_human_review.md")
        write_human_review(review_path, report, args.review_sample, args.seed)
        print(
            json.dumps(
                {"metrics": report["candidate"]["metrics"], "gates": report["gates"]},
                indent=2,
            )
        )
        print("Wrote", output)
        print("Wrote", review_path)
        return 0 if report["gates"]["pass"] else 1
    if args.judge_existing_report:
        output = Path(args.judge_existing_report).resolve()
        report = json.loads(output.read_text(encoding="utf-8"))
        validate_report(report)
        baseline = report.get("baseline")
        if not baseline:
            raise ValueError("Existing report has no baseline to judge")
        judge_progress = output.with_name(f"{output.stem}.judge.progress.jsonl")
        judge = JudgeClient(
            model=SFT_EVAL_JUDGE_MODEL,
            base_url=SFT_EVAL_JUDGE_BASE_URL,
            api_key=SFT_EVAL_JUDGE_API_KEY,
            timeout=SFT_EVAL_JUDGE_TIMEOUT,
            retries=args.judge_retries,
        )
        judgments, semantic = run_judge_batched(
            judge,
            report["candidate"]["records"],
            baseline["records"],
            orders=args.judge_orders,
            batch_size=args.judge_batch_size,
            progress_path=judge_progress,
        )
        report["judge"] = {
            "requested": True,
            "enabled": True,
            "status": "complete",
            "provider": SFT_EVAL_JUDGE_PROVIDER,
            "model": SFT_EVAL_JUDGE_MODEL,
            "orders": args.judge_orders,
            "batch_size": args.judge_batch_size,
            "summary": semantic,
            "judgments": judgments,
        }
        report["gates"] = release_gates(report["candidate"]["metrics"], semantic)
        validate_report(report)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        review_path = output.with_name(f"{output.stem}_human_review.md")
        write_human_review(review_path, report, args.review_sample, args.seed)
        judge_progress.unlink(missing_ok=True)
        print(json.dumps({"semantic": semantic, "gates": report["gates"]}, indent=2))
        print("Wrote", output)
        print("Wrote", review_path)
        return 0 if report["gates"]["pass"] else 1

    test_path = Path(args.test_set).resolve()
    all_items = load_jsonl(test_path)
    items = all_items[: args.limit] if args.limit else all_items
    if not items:
        raise ValueError("No evaluation examples selected")
    if args.judge and args.baseline == "none":
        raise ValueError("--judge requires --baseline for independent paired comparison")

    output = Path(args.output).resolve()
    progress_paths = {
        "candidate": output.with_name(f"{output.stem}.candidate.progress.jsonl"),
        "baseline": output.with_name(f"{output.stem}.baseline.progress.jsonl"),
        "judge": output.with_name(f"{output.stem}.judge.progress.jsonl"),
    }
    for progress_path in progress_paths.values():
        progress_path.unlink(missing_ok=True)

    created_at = utc_now()
    candidate_backend = make_backend(args.candidate, args)
    candidate_identity = candidate_backend.identity()
    candidate_records, candidate_metrics = run_model(
        candidate_backend,
        items,
        model_spec=args.candidate,
        max_tokens=args.max_tokens,
        progress_path=progress_paths["candidate"],
    )

    baseline_payload = None
    baseline_records: list[dict[str, Any]] = []
    if args.baseline != "none":
        baseline_backend = make_backend(args.baseline, args)
        baseline_identity = baseline_backend.identity()
        baseline_records, baseline_metrics = run_model(
            baseline_backend,
            items,
            model_spec=args.baseline,
            max_tokens=args.max_tokens,
            progress_path=progress_paths["baseline"],
        )
        baseline_payload = {
            "spec": args.baseline,
            "identity": baseline_identity,
            "artifact": artifact_fingerprint(args.baseline_artifact),
            "metrics": baseline_metrics,
            "records": baseline_records,
        }

    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "created_at": created_at,
        "dataset": {
            "path": str(test_path),
            "sha256": sha256_file(test_path),
            "declared_count": len(all_items),
            "evaluated_count": len(items),
        },
        "generation": {
            "temperature": 0.0,
            "seed": args.seed,
            "max_tokens": args.max_tokens,
        },
        "candidate": {
            "spec": args.candidate,
            "identity": candidate_identity,
            "artifact": artifact_fingerprint(args.candidate_artifact),
            "source_adapter": artifact_fingerprint(args.source_adapter_artifact),
            "metrics": candidate_metrics,
            "records": candidate_records,
        },
        "baseline": baseline_payload,
        "judge": {
            "requested": args.judge,
            "enabled": False,
            "status": "pending" if args.judge else "not_requested",
            "provider": SFT_EVAL_JUDGE_PROVIDER if args.judge else None,
            "model": SFT_EVAL_JUDGE_MODEL if args.judge else None,
            "orders": 0,
            "summary": None,
            "judgments": [],
        },
        "gates": release_gates(candidate_metrics),
    }
    validate_report(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.judge:
        print("Wrote deterministic checkpoint", output)
        judge = JudgeClient(
            model=SFT_EVAL_JUDGE_MODEL,
            base_url=SFT_EVAL_JUDGE_BASE_URL,
            api_key=SFT_EVAL_JUDGE_API_KEY,
            timeout=SFT_EVAL_JUDGE_TIMEOUT,
            retries=args.judge_retries,
        )
        judgments, semantic = run_judge_batched(
            judge,
            candidate_records,
            baseline_records,
            orders=args.judge_orders,
            batch_size=args.judge_batch_size,
            progress_path=progress_paths["judge"],
        )
        report["judge"].update(
            {
                "enabled": True,
                "status": "complete",
                "orders": args.judge_orders,
                "batch_size": args.judge_batch_size,
                "summary": semantic,
                "judgments": judgments,
            }
        )
        report["gates"] = release_gates(candidate_metrics, semantic)
        validate_report(report)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        semantic = None
    review_path = output.with_name(f"{output.stem}_human_review.md")
    write_human_review(review_path, report, args.review_sample, args.seed)
    print(json.dumps({"metrics": candidate_metrics, "semantic": semantic, "gates": report["gates"]}, indent=2))
    print("Wrote", output)
    print("Wrote", review_path)
    for progress_path in progress_paths.values():
        progress_path.unlink(missing_ok=True)
    return 0 if report["gates"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
