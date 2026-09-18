"""Poll SFT GATE-0 until training ends, fetch results, delete pod."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parents[1]
SESSION = REPO / "fine_tuning" / "kaggle" / "sft_session.json"
SSH_KEY = Path.home() / ".ssh" / "runpod_cpt"
INTERVAL_SEC = int(os.environ.get("SFT_MONITOR_INTERVAL_SEC", "900"))
MAX_WALL_HOURS = float(os.environ.get("SFT_MAX_WALL_HOURS", "8"))


def load_session() -> dict:
    return json.loads(SESSION.read_text(encoding="utf-8-sig"))


def ssh_cmd(session: dict, remote: str, timeout: int = 60) -> tuple[int, str]:
    if not session.get("ssh_host"):
        return 1, "no ssh_host"
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


def training_running(session: dict) -> bool:
    code, out = ssh_cmd(session, "pgrep -af train_sft_sota.py || true")
    for line in out.splitlines():
        if "train_sft_sota.py" in line and "pgrep" not in line and "bash -c" not in line:
            return True
    return False


def log_tail(session: dict, n: int = 20) -> str:
    _, out = ssh_cmd(session, f"tail -n {n} /workspace/sft_train.log 2>/dev/null || true")
    return out


def training_crashed(log: str, running: bool) -> bool:
    if running:
        return False
    tail = "\n".join(log.splitlines()[-15:])
    crash_markers = (
        "Traceback (most recent call last)",
        "RuntimeError:",
        "ImportError:",
        "CUDA out of memory",
    )
    return any(m in tail for m in crash_markers)


def training_finished(log: str, running: bool, stale_not_running: int) -> bool:
    if running:
        return False
    done_markers = (
        "SOTA SFT v2 complete",
        "Saved adapter to",
        "Run config:",
        "sft_run_config.json",
    )
    has_done = any(m in log for m in done_markers) or bool(re.search(r"train_runtime", log))
    if not has_done:
        return False
    # Require two consecutive not-running polls to avoid single-poll false positives.
    return stale_not_running >= 2


def sync_checkpoints() -> int:
    ps1 = SCRIPT_DIR / "sft_sync_checkpoints.ps1"
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1)],
        cwd=str(SCRIPT_DIR),
    )
    return proc.returncode


def fetch_results() -> int:
    sync_checkpoints()
    fetch = SCRIPT_DIR / "sft_fetch_artifacts.ps1"
    ps1 = fetch if fetch.is_file() else SCRIPT_DIR / "sft_fetch_results.ps1"
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1)],
        cwd=str(SCRIPT_DIR),
    )
    return proc.returncode


def delete_pod(pod_id: str) -> None:
    sys.path.insert(0, str(SCRIPT_DIR))
    from sft_provision_pod_mcp import http_json, load_mcp_token

    token = load_mcp_token()
    status, payload = http_json(f"https://rest.runpod.io/v1/pods/{pod_id}", token, method="DELETE")
    print("delete_pod", pod_id, "status", status, str(payload)[:300])
    if status not in (200, 201, 204):
        raise RuntimeError(f"Failed to delete pod {pod_id}: {payload}")


def main() -> None:
    session = load_session()
    pod_id = session["pod_id"]
    print("monitor_start", pod_id, "interval_sec", INTERVAL_SEC)
    print("ssh", f"{session.get('ssh_user', 'root')}@{session['ssh_host']}:{session.get('ssh_port', 22)}")

    stale_not_running = 0
    started = time.time()
    while True:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            wall_h = (time.time() - started) / 3600.0
            if MAX_WALL_HOURS > 0 and wall_h >= MAX_WALL_HOURS:
                print(f"[{ts}] max_wall {MAX_WALL_HOURS}h — sync, fetch, delete pod")
                fetch_results()
                delete_pod(pod_id)
                session["finished_at"] = ts
                session["monitor_status"] = "max_wall_pod_deleted"
                SESSION.write_text(json.dumps(session, indent=2), encoding="utf-8")
                print("MONITOR_DONE_MAX_WALL")
                return

            running = training_running(session)
            if running:
                stale_not_running = 0
            else:
                stale_not_running += 1
            log = log_tail(session, 40)
            print(f"[{ts}] running={running} stale={stale_not_running}", flush=True)
            if log:
                for line in log.splitlines()[-3:]:
                    print("  ", line[:160], flush=True)

            if training_crashed(log, running) and stale_not_running >= 1:
                print(f"[{ts}] training_crashed — fetch partial, delete pod (stop billing)")
                fetch_results()
                delete_pod(pod_id)
                session["finished_at"] = ts
                session["monitor_status"] = "crashed_pod_deleted"
                SESSION.write_text(json.dumps(session, indent=2), encoding="utf-8")
                print("MONITOR_DONE_CRASH")
                return

            rc = sync_checkpoints()
            if rc != 0:
                print(f"[{ts}] checkpoint_sync_warn exit={rc}", flush=True)

            if training_finished(log, running, stale_not_running):
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

        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    main()
