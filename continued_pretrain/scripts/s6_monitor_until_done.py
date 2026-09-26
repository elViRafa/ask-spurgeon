"""Poll S6/S7 continue-B until training ends, fetch results, delete pod. Never print secrets."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parents[1]
SESSION = REPO / "continued_pretrain" / "kaggle" / "runpod_cpt_v3" / "s6_session.json"
SSH_KEY = Path.home() / ".ssh" / "runpod_cpt"
INTERVAL_SEC = int(os.environ.get("S6_MONITOR_INTERVAL_SEC", "900"))
MAX_WALL_HOURS = float(os.environ.get("S6_MAX_WALL_HOURS", "16"))
DEFAULT_TOTAL_STEPS = 4128

DONE_MARKERS = (
    "COMPOSITE EARLY-STOP",
    "Training completed",
    "SOTA CPT v2 complete",
    "Saved run config",
    "theology_cpt_run_config.json",
)


def resolve_total_steps(cli_value: int | None = None) -> int:
    """Prefer CLI, then CPT_TOTAL_STEPS env, else S6 default 4128."""
    if cli_value is not None and int(cli_value) > 0:
        return int(cli_value)
    env_raw = (os.environ.get("CPT_TOTAL_STEPS") or "").strip()
    if env_raw:
        try:
            value = int(env_raw)
            if value > 0:
                return value
        except ValueError:
            pass
    return DEFAULT_TOTAL_STEPS


TOTAL_STEPS = resolve_total_steps()


def done_grep(total_steps: int | None = None) -> str:
    steps = int(total_steps if total_steps is not None else TOTAL_STEPS)
    return (
        "COMPOSITE EARLY-STOP|Saved run config|SOTA CPT v2 complete|"
        f"Training completed|{steps}/{steps}|theology_cpt_run_config.json"
    )


# Back-compat alias used by older callers / tests.
DONE_GREP = done_grep(DEFAULT_TOTAL_STEPS)


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
    """True if train process seen, False if definitely not, None on SSH flake."""
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


def log_done_scan(session: dict, total_steps: int | None = None) -> str:
    """Last 200 log lines plus any completion markers anywhere in the file."""
    grep = done_grep(total_steps)
    remote = (
        "tail -n 200 /workspace/cpt_train.log 2>/dev/null || true; "
        "echo '---MARKERS---'; "
        f"grep -E {grep!r} /workspace/cpt_train.log 2>/dev/null | tail -n 30 || true"
    )
    code, out = ssh_cmd(session, remote, timeout=90)
    if code != 0:
        print("ssh_warn log_done_scan", out[:200])
        return ""
    return out


def parse_step(log: str, total_steps: int | None = None) -> int | None:
    steps = int(total_steps if total_steps is not None else TOTAL_STEPS)
    matches = re.findall(rf"\|\s*(\d+)/{steps}\s*\[", log)
    if matches:
        return int(matches[-1])
    return None


def log_has_done_marker(log: str, total_steps: int | None = None) -> bool:
    if not log:
        return False
    if any(m in log for m in DONE_MARKERS):
        return True
    steps = int(total_steps if total_steps is not None else TOTAL_STEPS)
    if re.search(rf"\b{steps}/{steps}\b", log):
        return True
    return False


def training_finished(log: str, running: bool | None, total_steps: int | None = None) -> bool:
    """Done only when the process is gone AND a training completion marker is in the log.

    SSH flakes (running is None) never count as finished.
    """
    if running is not False:
        return False
    return log_has_done_marker(log, total_steps=total_steps)


def sync_checkpoints() -> int:
    ps1 = SCRIPT_DIR / "s6_sync_checkpoints.ps1"
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1)],
        cwd=str(SCRIPT_DIR),
    )
    return proc.returncode


def fetch_results() -> int:
    sync_checkpoints()
    ps1 = SCRIPT_DIR / "s6_fetch_results.ps1"
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1)],
        cwd=str(SCRIPT_DIR),
    )
    return proc.returncode


def delete_pod(pod_id: str) -> None:
    # Import token loader from provision script
    sys.path.insert(0, str(SCRIPT_DIR))
    from s6_provision_pod_mcp import http_json, load_mcp_token

    token = load_mcp_token()
    status, payload = http_json(f"https://rest.runpod.io/v1/pods/{pod_id}", token, method="DELETE")
    print("delete_pod", pod_id, "status", status, str(payload)[:300])
    if status not in (200, 201, 204):
        raise RuntimeError(f"Failed to delete pod {pod_id}: {payload}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Poll CPT continue-B until done")
    parser.add_argument(
        "--total-steps",
        type=int,
        default=None,
        help="Expected trainer max_steps (default CPT_TOTAL_STEPS or 4128)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    global TOTAL_STEPS, DONE_GREP
    args = parse_args(argv)
    TOTAL_STEPS = resolve_total_steps(args.total_steps)
    DONE_GREP = done_grep(TOTAL_STEPS)

    session = load_session()
    pod_id = session["pod_id"]
    print("monitor_start", pod_id, "interval_sec", INTERVAL_SEC, "total_steps", TOTAL_STEPS)
    print("ssh", f"{session.get('ssh_user', 'root')}@{session['ssh_host']}:{session.get('ssh_port', 22)}")

    stale_not_running = 0
    started = time.time()
    while True:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            wall_h = (time.time() - started) / 3600.0
            if MAX_WALL_HOURS > 0 and wall_h >= MAX_WALL_HOURS:
                print(f"[{ts}] max_wall {MAX_WALL_HOURS}h reached — sync, fetch, delete pod")
                fetch_results()
                delete_pod(pod_id)
                session["finished_at"] = ts
                session["monitor_status"] = "max_wall_pod_deleted"
                SESSION.write_text(json.dumps(session, indent=2), encoding="utf-8")
                print("MONITOR_DONE_MAX_WALL")
                return

            running = training_running(session)
            if running is None:
                print(f"[{ts}] ssh_flake — not counting as finished", flush=True)
                time.sleep(INTERVAL_SEC)
                continue
            if running:
                stale_not_running = 0
            else:
                stale_not_running += 1
            log_display = log_tail(session, 20)
            log = log_done_scan(session, total_steps=TOTAL_STEPS)
            step = parse_step(log_display or log, total_steps=TOTAL_STEPS)
            step_s = f"step={step}/{TOTAL_STEPS}" if step else "step=?"
            print(f"[{ts}] running={running} stale={stale_not_running} {step_s}", flush=True)
            if log_display:
                for line in log_display.splitlines()[-3:]:
                    print("  ", line[:160], flush=True)

            rc = sync_checkpoints()
            if rc != 0:
                print(f"[{ts}] checkpoint_sync_warn exit={rc}", flush=True)

            if training_finished(log, running, total_steps=TOTAL_STEPS):
                print(f"[{ts}] training_done — fetching results")
                rc = fetch_results()
                print("fetch_results exit", rc)
                print(f"[{ts}] deleting pod {pod_id}")
                delete_pod(pod_id)
                session["finished_at"] = ts
                session["monitor_status"] = "done_pod_deleted"
                SESSION.write_text(json.dumps(session, indent=2), encoding="utf-8")
                print("MONITOR_DONE")
                return
        except Exception as exc:
            print(f"[{ts}] monitor_error", exc, flush=True)
            if "Permission denied" in str(exc) or "publickey" in str(exc):
                print(f"[{ts}] ssh_blocked — add runpod_cpt.pub to Runpod account SSH keys", flush=True)

        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    main()
