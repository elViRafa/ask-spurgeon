"""Poll Vast S7 replay until training ends, fetch to vast_cpt_s7_replay, destroy instance.

Never print secrets. SSH flakes never count as finished.
Defaults: CPT_TOTAL_STEPS=955, session/results under vast_cpt_s7_replay.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parents[1]
SESSION = Path(
    os.environ.get(
        "VAST_SESSION_FILE",
        str(
            REPO
            / "continued_pretrain"
            / "kaggle"
            / "runpod_cpt_v3"
            / "vast_cpt_s7_replay_session.json"
        ),
    )
)
RESULTS_DIR = Path(
    os.environ.get(
        "VAST_LOCAL_RESULTS_DIR",
        str(REPO / "continued_pretrain" / "kaggle" / "runpod_cpt_v3" / "vast_cpt_s7_replay"),
    )
)
SSH_KEY = Path.home() / ".ssh" / "runpod_cpt"
INTERVAL_SEC = int(os.environ.get("VAST_CPT_MONITOR_INTERVAL_SEC", "600"))
MAX_WALL_HOURS = float(os.environ.get("VAST_CPT_MAX_WALL_HOURS", "12"))


def _reconfigure_stdio() -> None:
    """Windows cp1252 cannot print Unsloth progress bars (U+2588 block chars)."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError, TypeError):
            pass


def safe_line(text: str) -> str:
    """Strip non-ASCII so a redirected Windows log cannot UnicodeEncodeError."""
    return (text or "").encode("ascii", "replace").decode("ascii")

sys.path.insert(0, str(SCRIPT_DIR))
import s6_monitor_until_done as mon  # noqa: E402

# S7 default budget
os.environ.setdefault("CPT_TOTAL_STEPS", "955")
TOTAL_STEPS = mon.resolve_total_steps()
DONE_GREP = mon.done_grep(TOTAL_STEPS)


def load_session() -> dict:
    return json.loads(SESSION.read_text(encoding="utf-8"))


def ssh_cmd(session: dict, remote: str, timeout: int = 60) -> tuple[int, str]:
    host = session["ssh_host"]
    port = int(session.get("ssh_port") or 22)
    user = session.get("ssh_user") or "root"
    target = f"{user}@{host}"
    args = [
        "ssh",
        "-i",
        str(SSH_KEY),
        "-p",
        str(port),
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        f"ConnectTimeout={timeout}",
        target,
        remote,
    ]
    proc = subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout + 30,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out.strip()


def training_running(session: dict) -> bool | None:
    code, out = ssh_cmd(session, "pgrep -af train_cpt_sota.py || true")
    if code != 0:
        print("ssh_warn", out[:200])
        return None
    for line in out.splitlines():
        if "train_cpt_sota.py" in line and "pgrep" not in line and "bash -c" not in line:
            return True
    return False


def log_tail(session: dict, n: int = 15) -> str:
    _, out = ssh_cmd(session, f"tail -n {n} /workspace/cpt_train.log 2>/dev/null || true")
    return out


def log_done_scan(session: dict) -> str:
    remote = (
        "tail -n 200 /workspace/cpt_train.log 2>/dev/null || true; "
        "echo '---MARKERS---'; "
        f"grep -E {DONE_GREP!r} /workspace/cpt_train.log 2>/dev/null | tail -n 30 || true"
    )
    code, out = ssh_cmd(session, remote, timeout=90)
    if code != 0:
        print("ssh_warn log_done_scan", out[:200])
        return ""
    return out


def _run_ps1(name: str) -> int:
    env = os.environ.copy()
    env["VAST_SESSION_FILE"] = str(SESSION)
    env["VAST_LOCAL_RESULTS_DIR"] = str(RESULTS_DIR)
    ps1 = SCRIPT_DIR / name
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1)],
        cwd=str(SCRIPT_DIR),
        env=env,
    )
    return proc.returncode


def fetch_results() -> int:
    return _run_ps1("vast_cpt_s7_fetch.ps1")


def destroy_instance() -> int:
    destroy = REPO / "fine_tuning" / "scripts" / "vast_destroy.ps1"
    env = os.environ.copy()
    env["VAST_SESSION_FILE"] = str(SESSION)
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(destroy)],
        cwd=str(destroy.parent),
        env=env,
    )
    return proc.returncode


def main() -> None:
    session = load_session()
    inst = session.get("instance_id")
    print("monitor_start", inst, "interval_sec", INTERVAL_SEC, "total_steps", TOTAL_STEPS, flush=True)
    print(
        "ssh",
        f"{session.get('ssh_user', 'root')}@{session.get('ssh_host')}:{session.get('ssh_port', 22)}",
        flush=True,
    )
    print("results_dir", RESULTS_DIR, flush=True)

    started = time.time()
    while True:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            wall_h = (time.time() - started) / 3600.0
            if MAX_WALL_HOURS > 0 and wall_h >= MAX_WALL_HOURS:
                print(f"[{ts}] max_wall {MAX_WALL_HOURS}h reached — fetch + destroy")
                fetch_results()
                destroy_instance()
                print("MONITOR_DONE_MAX_WALL")
                return

            running = training_running(session)
            if running is None:
                print(f"[{ts}] ssh_flake — not counting as finished", flush=True)
                time.sleep(INTERVAL_SEC)
                continue
            log_display = log_tail(session, 20)
            log = log_done_scan(session)
            step = mon.parse_step(log_display or log)
            step_s = f"step={step}/{TOTAL_STEPS}" if step else "step=?"
            print(f"[{ts}] running={running} {step_s}", flush=True)
            if log_display:
                for line in log_display.splitlines()[-3:]:
                    print("  ", safe_line(line[:160]), flush=True)

            rc = fetch_results()
            if rc != 0:
                print(f"[{ts}] fetch_warn exit={rc}", flush=True)

            if mon.training_finished(log, running):
                print(f"[{ts}] training_done — fetching then destroy")
                fetch_results()
                destroy_instance()
                print("MONITOR_DONE")
                return
        except Exception as exc:
            print(f"[{ts}] monitor_error", exc, flush=True)
        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    _reconfigure_stdio()
    main()
