#!/usr/bin/env python3
"""Bulk assistant rewrite using the gold-pilot / knowledge-not-persona contract.

Does not call an API unless you pass --apply. Default is --dry-run.

Skips rows already in the gold overlay (qa_mix_manifest.json gold_overlay.source_lines).
Writes passing rows to a side JSONL; does not patch train until you merge later.

Usage (repo root):
  python -u fine_tuning/scripts/rewrite_qa_answers_teacher.py --dry-run --limit 3
  python -u fine_tuning/scripts/rewrite_qa_answers_teacher.py --apply --limit 3 --provider groq --model openai/gpt-oss-20b
  python -u fine_tuning/scripts/rewrite_qa_answers_teacher.py --apply --limit 50 --provider gemini
  python fine_tuning/scripts/review_qa_rewrite_bulk.py

Env: GROQ_API_KEY, GEMINI_API_KEY / GOOGLE_API_KEY, CEREBRAS_API_KEY,
     OPEN_ROUTER_API_KEY / OPENROUTER_API_KEY.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from build_qa_mix import is_refusal, read_jsonl, repo_root  # noqa: E402
from qa_rewrite_checks import check_assistant, role  # noqa: E402

TEACHER_SYSTEM = """You rewrite assistant answers for a theological Q&A training set on Spurgeon and the Puritans.

The user message is already in serve shape: headed CONTEXT plus QUESTION.
Rewrite ONLY the assistant answer. Do not invent facts, sermon numbers, or quotes.

Rules:
1. Knowledge voice, 2–6 sentences. Attribute in the third person ("Spurgeon teaches…", "the sermon argues…"). You are not Spurgeon and you do not speak as him or as any Puritan.
2. Do not address the reader with vocatives such as "Beloved", "My beloved", "Dear friends", or "My brethren". Do not use first-person preacher roleplay ("when I preached", "in my pulpit", "these lips must").
3. A light touch of the sources' register is welcome (scriptural cadence, concrete metaphor, careful distinction) so long as it never becomes costume.
4. Answer using ONLY the provided CONTEXT. If the question cannot be answered from it, refuse briefly and plainly (e.g. "These excerpts do not address…"). Do not quote mismatched sermons as if they answered. First-person is allowed only as the assistant's own limit ("I do not find this in the excerpts").
5. For answerable questions: include at least one quotation that is a verbatim copy-paste of a contiguous substring from CONTEXT, wrapped in ASCII double quotes. The quoted text must appear character-for-character inside CONTEXT (same words, punctuation, hyphens, commas, and spelling). Do NOT paraphrase, truncate, reword, or use ellipsis inside quotes. Pick a phrase that already exists exactly in CONTEXT—do not "clean up" or summarize it.
   BAD (paraphrased, will fail validation): "most thorough" when CONTEXT says "the most thorough change"
   BAD (truncated): "the profit that he makes by it," when CONTEXT says "the profit that he makes by it, is not worth the risk"
   GOOD (exact substring): "the most thorough change" copied directly from CONTEXT
   GOOD (exact substring): "battle-field of sin." including the hyphen and period, copied directly from CONTEXT
6. Cite [Sermon N] only when that exact header number appears in CONTEXT.
7. Return JSON only: {"answer": "<assistant text>"}
"""

DEFAULT_MODELS = {
    "groq": "openai/gpt-oss-120b",
    # Free-tier OpenRouter: many :free slugs rotate; openrouter/free auto-routes.
    "openrouter": "openrouter/free",
    "gemini": "gemini-2.5-flash",
    "cerebras": "gpt-oss-120b",
    "ollama": "spurgeon-cpt",
}

TEACHER_TIMEOUT_S = 75
TEACHER_RETRIES = 4
CONSECUTIVE_FAIL_ABORT = 3
# Cap 429 backoff so a dead provider does not burn ~10 min per row.
TEACHER_429_MAX_WAIT_S = 45


def _log(msg: str) -> None:
    print(msg, flush=True)


def _provider_key(provider: str) -> str:
    load_dotenv()
    if provider == "openrouter":
        return os.getenv("OPEN_ROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY") or ""
    if provider == "groq":
        return os.getenv("GROQ_API_KEY") or ""
    if provider == "gemini":
        return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    if provider == "cerebras":
        return os.getenv("CEREBRAS_API_KEY") or ""
    if provider == "ollama":
        return "ollama"  # local; no cloud key
    return ""


def _default_model(provider: str, model: str) -> str:
    return model or DEFAULT_MODELS[provider]


def _extract_chat_content(data: dict) -> str:
    """Parse OpenAI-compatible chat/completions JSON; tolerate provider quirks."""
    choices = data.get("choices")
    if not choices:
        err = data.get("error")
        if err:
            raise RuntimeError(f"API error: {err}")
        raise RuntimeError(f"empty choices: {json.dumps(data)[:400]}")
    choice = choices[0]
    msg = choice.get("message") or {}
    for key in ("content", "text"):
        val = msg.get(key)
        if val is not None and str(val).strip():
            return str(val)
    # gpt-oss on Cerebras sometimes returns reasoning-only when content is null.
    reasoning = msg.get("reasoning")
    if reasoning is not None and str(reasoning).strip():
        return str(reasoning)
    legacy = choice.get("text")
    if legacy is not None and str(legacy).strip():
        return str(legacy)
    finish = choice.get("finish_reason") or data.get("finish_reason")
    raise KeyError(
        f"message missing content (finish_reason={finish!r}): "
        f"{json.dumps(msg)[:400]}"
    )


def _openai_compatible_chat(
    *,
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    timeout: float = TEACHER_TIMEOUT_S,
    system_prompt: str | None = None,
    max_tokens: int = 500,
    temperature: float = 0.4,
) -> str:
    import requests

    url = base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    # OpenRouter prefers HTTP-Referer / X-Title for rankings; harmless elsewhere.
    if "openrouter.ai" in base_url:
        headers["HTTP-Referer"] = "https://github.com/search-sermons"
        headers["X-Title"] = "ask-spurgeon-qa-rewrite"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt or TEACHER_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    last_err: Exception | None = None
    for attempt in range(1, TEACHER_RETRIES + 1):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if r.status_code == 429:
                retry_after = r.headers.get("Retry-After")
                if retry_after and str(retry_after).isdigit():
                    wait = min(TEACHER_429_MAX_WAIT_S, int(retry_after))
                else:
                    wait = min(TEACHER_429_MAX_WAIT_S, 10 * (2 ** (attempt - 1)))
                _log(f"  429 rate limit; sleep {wait}s (attempt {attempt}/{TEACHER_RETRIES})")
                time.sleep(wait)
                last_err = RuntimeError(f"429: {r.text[:200]}")
                continue
            if r.status_code in (401, 402, 403, 404):
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
            r.raise_for_status()
            body = r.json()
            try:
                content = _extract_chat_content(body)
            except (KeyError, RuntimeError, TypeError, json.JSONDecodeError) as e:
                last_err = e
                wait = min(30, attempt * 3)
                _log(
                    f"  bad response shape: {e}; sleep {wait}s "
                    f"(attempt {attempt}/{TEACHER_RETRIES})"
                )
                time.sleep(wait)
                continue
            return content
        except RuntimeError:
            raise
        except Exception as e:
            last_err = e
            wait = min(30, attempt * 3)
            _log(f"  teacher error: {e}; sleep {wait}s (attempt {attempt}/{TEACHER_RETRIES})")
            time.sleep(wait)
    raise RuntimeError(f"teacher failed after {TEACHER_RETRIES} tries: {last_err}")


def call_teacher(
    provider: str,
    model: str,
    user_content: str,
    slice_name: str,
    *,
    system_prompt: str | None = None,
    max_tokens: int = 500,
    temperature: float = 0.4,
) -> str:
    extra = ""
    if slice_name == "refusal":
        extra = (
            "\nThis example is an insufficient-context / mismatch case. "
            "Refuse honestly. Do not quote the sermons as if they answered the question.\n"
        )
    prompt = extra + user_content
    key = _provider_key(provider)
    if not key:
        raise SystemExit(f"ERROR: missing API key for provider={provider}")
    model = _default_model(provider, model)
    chat_kwargs = {
        "api_key": key,
        "model": model,
        "prompt": prompt,
        "system_prompt": system_prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    if provider == "openrouter":
        return _openai_compatible_chat(
            base_url="https://openrouter.ai/api/v1",
            **chat_kwargs,
        )

    if provider == "groq":
        return _openai_compatible_chat(
            base_url="https://api.groq.com/openai/v1",
            **chat_kwargs,
        )

    if provider == "cerebras":
        return _openai_compatible_chat(
            base_url="https://api.cerebras.ai/v1",
            **chat_kwargs,
        )

    if provider == "gemini":
        # OpenAI-compatible Gemini endpoint (AI Studio).
        return _openai_compatible_chat(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai",
            **chat_kwargs,
        )

    if provider == "ollama":
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        return _openai_compatible_chat(
            base_url=f"{host.rstrip('/')}/v1",
            timeout=180,
            **chat_kwargs,
        )

    raise SystemExit(f"unknown provider {provider}")


def parse_answer(raw: str) -> str:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json\n", "", 1).strip()
    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and "answer" in obj:
            return str(obj["answer"]).strip()
    except json.JSONDecodeError:
        pass
    return text


def skipped_lines(manifest: dict) -> set[int]:
    overlay = manifest.get("gold_overlay") or {}
    return {int(n) for n in overlay.get("source_lines") or []}


def _write_rec(
    *,
    line_no: int,
    slice_name: str,
    provider: str,
    model: str,
    system: str,
    user: str,
    answer: str,
    errs: list[str],
) -> dict:
    return {
        "source_line": line_no,
        "slice": slice_name,
        "teacher": provider,
        "model": model,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "ok": not errs,
        "errors": errs,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
            {"role": "assistant", "content": answer},
        ],
    }


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description="Bulk rewrite SFT assistants (gold contract)")
    p.add_argument("--dry-run", action="store_true", default=False)
    p.add_argument("--apply", action="store_true", help="Call the teacher API")
    p.add_argument("--limit", type=int, default=3, help="Max new rows this run")
    p.add_argument(
        "--provider",
        choices=("openrouter", "groq", "gemini", "cerebras", "ollama"),
        default="groq",
    )
    p.add_argument("--model", default="")
    p.add_argument("--sleep", type=float, default=1.0)
    p.add_argument(
        "--rerun-ok",
        action="store_true",
        help="Re-call the teacher for ok=true rows already in --output",
    )
    p.add_argument(
        "--retry-drops",
        action="store_true",
        help="Re-attempt rows already in --output with ok=false (skip only ok=true lines)",
    )
    p.add_argument(
        "--output",
        default=str(
            repo_root() / "fine_tuning" / "data" / "qa_rewrite_pilot" / "bulk_pending.jsonl"
        ),
    )
    args = p.parse_args(argv)
    if args.apply and args.dry_run:
        print("ERROR: use either --dry-run or --apply, not both", file=sys.stderr)
        return 2
    dry = not args.apply
    model = _default_model(args.provider, args.model)

    repo = repo_root()
    data = repo / "fine_tuning" / "data"
    train = read_jsonl(data / "qa_mix_train.jsonl")
    manifest = json.loads((data / "qa_mix_manifest.json").read_text(encoding="utf-8"))
    skip = skipped_lines(manifest)

    out_path = Path(args.output)

    if args.rerun_ok:
        if not out_path.exists():
            print(f"ERROR: missing {out_path}", file=sys.stderr)
            return 2
        pending = read_jsonl(out_path)
        ok_recs = [r for r in pending if r.get("ok") is True]
        rerun_limit = args.limit if "--limit" in sys.argv else len(ok_recs)
        _log(
            f"rerun_ok pending={len(pending)} ok={len(ok_recs)} limit={rerun_limit} "
            f"dry_run={dry} provider={args.provider} model={model}"
        )
        if dry:
            for rec in ok_recs[:rerun_limit]:
                _log(f"--- line {rec.get('source_line')} {rec.get('slice')}")
            _log("Dry-run only. Next: --apply --rerun-ok --provider groq")
            return 0
        n_ok = 0
        n_drop = 0
        updated: list[dict] = []
        ok_left = rerun_limit
        for rec in pending:
            if rec.get("ok") is not True or ok_left <= 0:
                updated.append(rec)
                continue
            ok_left -= 1
            user = role(rec["messages"], "user")
            slice_name = rec.get("slice") or "answerable"
            line_no = int(rec["source_line"])
            idx = line_no - 1
            train_sys = (
                role(train[idx]["messages"], "system")
                if 0 <= idx < len(train)
                else role(rec["messages"], "system")
            )
            try:
                raw = call_teacher(args.provider, model, user, slice_name)
            except Exception as e:
                print(f"ERROR line {line_no}: {e}", file=sys.stderr, flush=True)
                rec = dict(rec)
                rec["ok"] = False
                rec["errors"] = [str(e)]
                updated.append(rec)
                n_drop += 1
                continue
            answer = parse_answer(raw)
            errs = check_assistant(user, answer, slice_name)
            updated.append(
                _write_rec(
                    line_no=line_no,
                    slice_name=slice_name,
                    provider=args.provider,
                    model=model,
                    system=train_sys,
                    user=user,
                    answer=answer,
                    errs=errs,
                )
            )
            if errs:
                n_drop += 1
                _log(f"DROP line {line_no}: {errs[0]}")
            else:
                n_ok += 1
                _log(f"OK   line {line_no} {slice_name} chars={len(answer)}")
            time.sleep(args.sleep)
        tmp = out_path.with_suffix(".jsonl.tmp")
        with tmp.open("w", encoding="utf-8") as f:
            for rec in updated:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        tmp.replace(out_path)
        _log(f"Rewrote {out_path} rerun ok={n_ok} dropped={n_drop}")
        _log("Do not merge into train until review_qa_rewrite_bulk.py PASS on ok rows.")
        return 0

    done_keys: set[int] = set()
    if out_path.exists():
        for prev in read_jsonl(out_path):
            if args.retry_drops:
                if prev.get("ok") is True:
                    done_keys.add(int(prev["source_line"]))
            else:
                done_keys.add(int(prev["source_line"]))

    candidates: list[tuple[int, dict, str]] = []
    for i, row in enumerate(train, start=1):
        if i in skip or i in done_keys:
            continue
        slice_name = "refusal" if is_refusal(row) else "answerable"
        candidates.append((i, row, slice_name))
        if len(candidates) >= args.limit:
            break

    _log(
        f"train={len(train)} skip_gold={len(skip)} already_pending={len(done_keys)} "
        f"this_run={len(candidates)} dry_run={dry} provider={args.provider} model={model}"
    )
    if dry:
        for i, row, slice_name in candidates:
            user = role(row["messages"], "user")
            _log(f"--- line {i} {slice_name} user_chars={len(user)}")
            _log(user[:240].replace("\n", " ") + "...")
        _log("Dry-run only. Next: --apply --limit 3 --provider groq --model openai/gpt-oss-20b")
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    n_ok = 0
    n_drop = 0
    consecutive_api_fail = 0
    with out_path.open("a", encoding="utf-8") as f:
        for i, row, slice_name in candidates:
            user = role(row["messages"], "user")
            try:
                raw = call_teacher(args.provider, model, user, slice_name)
                consecutive_api_fail = 0
            except Exception as e:
                print(f"ERROR line {i}: {e}", file=sys.stderr, flush=True)
                n_drop += 1
                consecutive_api_fail += 1
                if consecutive_api_fail >= CONSECUTIVE_FAIL_ABORT:
                    _log(
                        f"Abort: {CONSECUTIVE_FAIL_ABORT} consecutive API failures "
                        f"(provider exhausted?). ok={n_ok} dropped={n_drop}"
                    )
                    break
                continue
            answer = parse_answer(raw)
            errs = check_assistant(user, answer, slice_name)
            rec = _write_rec(
                line_no=i,
                slice_name=slice_name,
                provider=args.provider,
                model=model,
                system=role(row["messages"], "system"),
                user=user,
                answer=answer,
                errs=errs,
            )
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            if errs:
                n_drop += 1
                _log(f"DROP line {i}: {errs[0]}")
            else:
                n_ok += 1
                _log(f"OK   line {i} {slice_name} chars={len(answer)}")
            time.sleep(args.sleep)
    _log(f"Wrote {out_path} ok={n_ok} dropped={n_drop}")
    _log("Do not merge into train until review_qa_rewrite_bulk.py PASS on ok rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
