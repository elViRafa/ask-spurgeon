"""Poll every 20 min for US-IL-1 4090 + volume; provision and launch S6 when available."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parents[1]
SESSION = REPO / "continued_pretrain" / "kaggle" / "runpod_cpt_v3" / "s6_session.json"
LOG = REPO / "continued_pretrain" / "kaggle" / "runpod_cpt_v3" / "s6_capacity_watch.log"
INTERVAL_SEC = int(os.environ.get("S6_CAPACITY_INTERVAL_SEC", "1200"))  # 20 min

sys.path.insert(0, str(SCRIPT_DIR))
from s6_provision_pod_mcp import (  # noqa: E402
    load_mcp_token,
    load_session,
    pod_exists,
    save_session,
    try_provision_pod,
    wait_ssh,
)
from s6_monitor_until_done import ssh_cmd, training_running  # noqa: E402

PUBKEY = Path.home() / ".ssh" / "runpod_cpt.pub"


def log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def run_ps1(name: str, *extra: str) -> int:
    ps1 = SCRIPT_DIR / name
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(ps1),
        *extra,
    ]
    log("run " + " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(SCRIPT_DIR))
    return proc.returncode


def orchestrate_training() -> bool:
    steps = [
        ("s6_wait_ssh.ps1", []),
        ("s6_verify_mount.ps1", []),
        ("s6_sync_to_pod.ps1", []),
        ("s6_launch_continue_b.ps1", []),
        ("s6_start_monitor.ps1", []),
    ]
    for script, args in steps:
        rc = run_ps1(script, *args)
        if rc != 0:
            log(f"FAILED {script} exit={rc}")
            return False
    return True


def session_has_live_pod(session: dict, token: str) -> bool:
    pod_id = session.get("pod_id")
    if not pod_id:
        return False
    return pod_exists(token, str(pod_id))


def maybe_resolve_ssh(session: dict, token: str) -> dict:
    pod_id = str(session.get("pod_id") or "")
    if not pod_id:
        return session
    if session.get("ssh_host") and session.get("ssh_user"):
        return session
    try:
        ssh_info = wait_ssh(token, pod_id, timeout_min=5)
        session.update(ssh_info)
        save_session(session)
        log(f"ssh_ready {ssh_info['ssh_user']}@{ssh_info['ssh_host']}")
    except Exception as exc:
        log(f"ssh_wait_warn {exc}")
    return session


def training_already_running(session: dict) -> bool:
    if not session.get("ssh_host"):
        return False
    try:
        return training_running(session)
    except Exception as exc:
        log(f"training_check_warn {exc}")
        return False


def watch_once(token: str) -> str:
    """Return: waiting | provisioned | training | done"""
    session = load_session()
    status = session.get("watch_status") or session.get("monitor_status") or ""

    if status in ("done_pod_deleted", "training_launched"):
        log("WATCH_DONE prior run complete")
        return "done"

    if session_has_live_pod(session, token):
        session = maybe_resolve_ssh(session, token)
        if training_already_running(session):
            log("WATCH_HANDOFF training already running — starting monitor")
            session["watch_status"] = "training_running"
            save_session(session)
            run_ps1("s6_start_monitor.ps1")
            return "training"
        log("pod live but training not running — orchestrating")
        if orchestrate_training():
            session = load_session()
            session["watch_status"] = "training_launched"
            save_session(session)
            log("WATCH_OK training launched")
            return "training"
        return "waiting"

    pubkey = PUBKEY.read_text(encoding="utf-8").strip()
    log("no live pod — probing 4090 US-IL-1 + volume availability")
    result = try_provision_pod(token, pubkey)
    if not result:
        log("WATCH_WAIT no 4090 capacity in US-IL-1 (volume 7hb931c5oe)")
        session["watch_status"] = "waiting_capacity"
        session["pod_id"] = None
        save_session(session)
        return "waiting"

    pod_id, meta = result
    meta["watch_status"] = "provisioned"
    save_session(meta)
    log(f"WATCH_PROVISIONED pod={pod_id} image={meta.get('image_name')}")

    if orchestrate_training():
        session = load_session()
        session["watch_status"] = "training_launched"
        save_session(session)
        log("WATCH_OK provisioned and training launched")
        return "training"

    log("WATCH_WARN provisioned but orchestrate failed — will retry next poll")
    return "waiting"


def main() -> None:
    log(f"capacity_watch_start interval_sec={INTERVAL_SEC}")
    token = load_mcp_token()
    while True:
        try:
            state = watch_once(token)
            if state in ("training", "done"):
                log(f"capacity_watch_exit state={state}")
                return
        except Exception as exc:
            log(f"capacity_watch_error {exc}")
        log(f"sleep {INTERVAL_SEC}s")
        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    main()
