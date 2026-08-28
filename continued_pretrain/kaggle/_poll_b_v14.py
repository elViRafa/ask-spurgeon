"""B v14 resume poller — stop on ERROR (hand off to other Kaggle user); no retry."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime, timezone

KERNEL = "rafaelvieira1/theology-cpt-v2-b-training-sota"
OUT = os.path.join(os.path.dirname(__file__), "b_logs_v14_raw.txt")
KEYS = (
    "Auto-resume",
    "PREV_RUN_CHECKPOINT",
    "Resuming from",
    "D1 ",
    "D2 ",
    "multi_doc_rows",
    "GATE FAIL",
    "Eval metric keys step=",
    "eval_spurgeon_loss=",
    "NOTE: eval_spurgeon_loss rose",
    "TrainOutput",
    "Traceback",
    "DeadKernelError",
    "OutOfMemory",
    "Starting SOTA",
)

env = os.environ.copy()
env["PYTHONUTF8"] = "1"
env["PYTHONIOENCODING"] = "utf-8"


def status() -> str:
    p = subprocess.run(
        [sys.executable, "-m", "kaggle", "kernels", "status", KERNEL],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=60,
    )
    return (p.stdout + p.stderr).strip()


def terminal(st: str) -> bool:
    low = st.lower()
    return any(x in low for x in ("complete", "error", "cancel", "fail"))


def main() -> int:
    seen = 0
    with open(OUT, "a", encoding="utf-8", errors="replace") as f:
        while True:
            now = datetime.now(timezone.utc).strftime("%H:%M:%SZ")
            try:
                st = status()
            except Exception as e:
                st = f"status error: {e}"
            print(f"[{now}] {st}", flush=True)
            if terminal(st) and "status error" not in st.lower():
                ok = "complete" in st.lower() and "error" not in st.lower()
                print("TERMINAL", "OK" if ok else "STOP_NO_RETRY", flush=True)
                return 0 if ok else 1
            p = subprocess.Popen(
                [sys.executable, "-m", "kaggle", "kernels", "logs", KERNEL, "-f"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                bufsize=1,
            )
            assert p.stdout is not None
            try:
                for line in p.stdout:
                    f.write(line)
                    f.flush()
                    if any(k in line for k in KEYS):
                        safe = line.rstrip().encode("ascii", "replace").decode("ascii")
                        print(safe, flush=True)
                    seen += 1
            except Exception as e:
                print(f"follow error: {e}", flush=True)
            p.wait()
            time.sleep(40)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
