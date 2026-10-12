#!/usr/bin/env python3
"""Upload S8 m_hi resume merged 16-bit HF to a **new** Hub repo (not production LoRA v2)."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_MERGED = REPO / "fine_tuning/models/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit"
DEFAULT_HF_REPO = "rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit"

MODEL_CARD = """---
license: other
base_model: unsloth/Qwen3.5-4B-Base
tags:
  - theology
  - continued-pretraining
  - experimental
library_name: transformers
---

# Qwen3.5-4B theology CPT — S8 m_hi resume (merged 16-bit, experimental)

**Not production.** Hub LoRA v2 (`rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2`, Phase A `06354dfc`) stays canonical until isolation C wins §5.

## Provenance

| Field | Value |
|-------|--------|
| Resume LoRA SHA | `2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207` |
| Step | 2250 (m_hi resume) |
| Merge parent | P0 s5best `a70fded8` on `a_output_v6_p0` |
| Merge | Two-stage 16-bit (`merge_cpt_s8_mhi_resume.py`) |
| Isolation C | 2026-10-07 — §5 **miss** (puritan loss 1.6605 vs 1.6349) |

## Isolation C (a_output_v6_p0 holdouts, vs stock base)

| Bucket | Δ PPL |
|--------|-------|
| Spurgeon | −17.0% |
| Puritan | −12.8% |
| Confession | −10.7% |
| General | **+3.8%** (worse than base) |

## Load

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained("REPO_ID", torch_dtype="auto", device_map="auto", trust_remote_code=True)
tokenizer = AutoTokenizer.from_pretrained("REPO_ID", trust_remote_code=True)
```

Tokenizer must come from this merged folder (not a stale Ollama export).
"""


def _token() -> str | None:
    for key in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
        val = (os.environ.get(key) or "").strip()
        if val:
            return val
    dotenv = REPO / ".env"
    if dotenv.is_file():
        for line in dotenv.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("HF_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'") or None
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged-path", type=Path, default=DEFAULT_MERGED)
    parser.add_argument("--repo-id", default=DEFAULT_HF_REPO)
    parser.add_argument("--public", action="store_true", help="Create/upload as public repo")
    parser.add_argument("--dry-run", action="store_true", help="Write README only, no upload")
    args = parser.parse_args()

    merged = args.merged_path.resolve()
    if not (merged / "config.json").is_file():
        print(f"FAIL: merged model missing at {merged}")
        print("Run merge_cpt_s8_mhi_resume.py on Ampere first.")
        sys.exit(1)

    readme = merged / "README.md"
    card = MODEL_CARD.replace("REPO_ID", args.repo_id)
    readme.write_text(card, encoding="utf-8")
    print("Wrote", readme)

    if args.dry_run:
        print("dry-run: skip Hub upload")
        return

    token = _token()
    if not token:
        print("FAIL: set HF_TOKEN in .env or environment")
        sys.exit(1)

    from huggingface_hub import HfApi

    api = HfApi(token=token)
    api.create_repo(repo_id=args.repo_id, repo_type="model", exist_ok=True, private=not args.public)
    api.upload_folder(
        folder_path=str(merged),
        repo_id=args.repo_id,
        repo_type="model",
        commit_message="Upload S8 m_hi resume merged 16-bit (experimental, §5 miss)",
    )
    print("Upload complete:", f"https://huggingface.co/{args.repo_id}")


if __name__ == "__main__":
    main()
