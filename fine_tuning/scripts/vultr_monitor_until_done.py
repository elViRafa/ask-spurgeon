"""Poll Vultr GATE-0 until SFT ends, fetch artifacts, delete the instance."""
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
SESSION = REPO / "fine_tuning" / "kaggle" / "vultr_sft_session.json"
SSH_KEY = Path.home() / ".ssh" / "runpod_cpt"
INTERVAL_SEC = int(os.environ.get("VULTR_MONITOR_INTERVAL_SEC", "300"))
MAX_WALL_HOURS = float(os.environ.get("VULTR_MAX_WALL_HOURS", "8"))
SETUP_GRACE_MIN = float(os.environ.get("VULTR_SETUP_GRACE_MIN", "70"))


def load_session() -> dict:
    return json.loads(SESSION.read_text(encoding="utf-8-sig"))


def save_session(session: dict) -> None:
    SESSION.write_text(json.dumps(session, indent=2), encoding="utf-8")


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
        "-o",
        "BatchMode=yes",
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
    _, out = ssh_cmd(session, "pgrep -af train_sft_sota.py || true")
    for line in out.splitlines():
        if "train_sft_sota.py" in line and "pgrep" not in line and "bash -c" not in line:
            return True
    return False


def pipeline_running(session: dict) -> bool:
    if training_running(session):
        return True
    _, out = ssh_cmd(session, "pgrep -af sft_remote_train.sh || true")
    for line in out.splitlines():
        if "sft_remote_train.sh" in line and "pgrep" not in line:
            return True
    return False


def log_tail(session: dict, path: str, n: int = 40) -> str:
    _, out = ssh_cmd(session, f"tail -n {n} {path} 2>/dev/null || true")
    return out


def training_crashed(log: str, running: bool) -> bool:
    if running:
        return False
    tail = "\n".join(log.splitlines()[-20:])
    crash_markers = (
        "Traceback (most recent call last)",
        "RuntimeError:",
        "ImportError:",
        "CUDA out of memory",
        "SMOKE FAIL",
        "preflight FAIL",
        "merge FAIL",
        "SHA256 mismatch",
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
    return stale_not_running >= 2


def run_ps1(name: str, extra: list[str] | None = None) -> int:
    ps1 = SCRIPT_DIR / name
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(ps1),
    ]
    if extra:
        cmd.extend(extra)
    proc = subprocess.run(cmd, cwd=str(SCRIPT_DIR))
    return proc.returncode


def fetch_results(partial: bool = True) -> int:
    extra = ["-PartialOnly"] if partial else []
    return run_ps1("vultr_fetch.ps1", extra)


def delete_instance() -> None:
    rc = run_ps1("vultr_destroy.ps1", ["-Force"])
    print("delete_instance exit", rc)
    if rc not in (0,):
        raise RuntimeError(f"vultr_destroy.ps1 exit {rc}")


def combined_logs(session: dict) -> str:
    launch = log_tail(session, "/workspace/sft_launch.log", 80)
    train = log_tail(session, "/workspace/sft_train.log", 80)
    return launch + "\n" + train


def setup_failed(logs: str, wall_min: float, running: bool) -> bool:
    if running:
        return False
    if "SMOKE FAIL" in logs:
        return True
    if wall_min >= SETUP_GRACE_MIN and "SETUP_OK" not in logs:
        return True
    return False


def finish(session: dict, status: str, marker: str) -> None:
    session["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    session["monitor_status"] = status
    save_session(session)
    print(marker)


def main() -> None:
    session = load_session()
    inst = session.get("instance_id")
    print("monitor_start", inst, "interval_sec", INTERVAL_SEC)
    print("ssh", f"{session.get('ssh_user', 'root')}@{session.get('ssh_host')}:{session.get('ssh_port', 22)}")

    stale_not_running = 0
    started = time.time()
    while True:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            session = load_session()
            wall_h = (time.time() - started) / 3600.0
            wall_min = (time.time() - started) / 60.0
            if MAX_WALL_HOURS > 0 and wall_h >= MAX_WALL_HOURS:
                print(f"[{ts}] max_wall {MAX_WALL_HOURS}h — fetch, delete")
                fetch_results(partial=True)
                delete_instance()
                finish(session, "max_wall_deleted", "MONITOR_DONE_MAX_WALL")
                return

            running = pipeline_running(session)
            train_run = training_running(session)
            if running:
                stale_not_running = 0
            else:
                stale_not_running += 1
            logs = combined_logs(session)
            train_log = log_tail(session, "/workspace/sft_train.log", 40)
            print(f"[{ts}] pipeline={running} train={train_run} stale={stale_not_running}", flush=True)
            if logs:
                for line in logs.splitlines()[-4:]:
                    print("  ", line[:160], flush=True)

            if setup_failed(logs, wall_min, running):
                print(f"[{ts}] setup/smoke failed — fetch logs, destroy")
                fetch_results(partial=True)
                delete_instance()
                finish(session, "setup_failed_deleted", "MONITOR_DONE_SETUP_FAIL")
                sys.exit(1)

            if training_crashed(train_log + "\n" + logs, train_run) and stale_not_running >= 1:
                print(f"[{ts}] training_crashed — fetch partial, destroy")
                fetch_results(partial=True)
                delete_instance()
                finish(session, "crashed_deleted", "MONITOR_DONE_CRASH")
                sys.exit(1)

            rc = fetch_results(partial=True)
            if rc != 0:
                print(f"[{ts}] fetch_warn exit={rc}", flush=True)

            if training_finished(train_log, train_run, stale_not_running):
                print(f"[{ts}] training_done — fetching results")
                rc = fetch_results(partial=True)
                print("fetch_results exit", rc)
                print(f"[{ts}] deleting instance {inst}")
                delete_instance()
                finish(session, "done_deleted", "MONITOR_DONE")
                return
        except Exception as exc:
            print(f"[{ts}] monitor_error", exc, flush=True)

        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    main()
