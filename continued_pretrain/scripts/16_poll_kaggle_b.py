#!/usr/bin/env python3
"""Poll Kaggle CPT B kernel every 5 minutes until complete/failed."""

from __future__ import annotations

import re
import subprocess
import sys
import time
from datetime import datetime, timezone

KERNEL = "rafaelvieira1/theology-cpt-v2-c-eval-sota"
POLL_S = 300


def status() -> str:
    p = subprocess.run(
        [sys.executable, "-m", "kaggle", "kernels", "status", KERNEL],
        capture_output=True,
        text=True,
        timeout=60,
    )
    return (p.stdout + p.stderr).strip()


def log_snippet() -> str:
    try:
        p = subprocess.run(
            [sys.executable, "-m", "kaggle", "kernels", "logs", KERNEL],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=90,
        )
    except subprocess.TimeoutExpired:
        return "(log fetch timeout)"
    text = p.stdout + p.stderr
    keys = [
        "GPU:",
        "CUDA smoke",
        "SRC_DATASET_PATH",
        "train rows",
        "FileNotFoundError",
        "AcceleratorError",
        "P100",
        "Tesla T4",
        "loss",
        "Saving",
        "ERROR",
        "Traceback",
        "ADAPTER_PATH",
        "Using ADAPTER_PATH",
        "MCQ",
        "ppl",
        "eval_mix",
    ]
    hits = []
    for k in keys:
        for m in re.finditer(re.escape(k) + ".{0,120}", text):
            hits.append(m.group(0).replace("\n", " ")[:160])
    return " | ".join(hits[:8]) if hits else f"(log bytes={len(text)})"


def main() -> int:
    while True:
        now = datetime.now(timezone.utc).strftime("%H:%M:%SZ")
        try:
            st = status()
        except Exception as e:
            st = f"status error: {e}"
        print(f"[{now}] {st}", flush=True)
        try:
            print(f"  hints: {log_snippet()}", flush=True)
        except Exception as e:
            print(f"  log fetch skipped: {e}", flush=True)
        low = st.lower()
        if "complete" in low and "error" not in low:
            print("SUCCESS", flush=True)
            return 0
        if any(x in low for x in ("error", "failed", "cancelled")):
            print("FAILED", flush=True)
            return 1
        time.sleep(POLL_S)


if __name__ == "__main__":
    raise SystemExit(main())
