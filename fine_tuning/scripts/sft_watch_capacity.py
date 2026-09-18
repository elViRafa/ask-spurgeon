"""Poll US-IL-1 for 4090/L40S + volume; launch SFT when available.

Billing rules:
- No pod while waiting for capacity (probe only hits create API on success path).
- If pod is provisioned but idle (no train/merge), retry orchestration then delete after timeout.
- Pull long GPU artifacts locally during training and before pod delete.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parents[1]
LOG = REPO / "fine_tuning" / "kaggle" / "sft_capacity_watch.log"
INTERVAL_SEC = int(os.environ.get("SFT_CAPACITY_INTERVAL_SEC", "600"))
SSH_WAIT_MIN = int(os.environ.get("SFT_CAPACITY_SSH_WAIT_MIN", "25"))
ORCHESTRATE_RETRIES = int(os.environ.get("SFT_ORCHESTRATE_RETRIES", "3"))

sys.path.insert(0, str(SCRIPT_DIR))
from sft_monitor_until_done import ssh_cmd, training_running  # noqa: E402
from sft_pod_lifecycle import (  # noqa: E402
    cleanup_idle_pod,
    fetch_local_artifacts,
    gpu_work_running,
    load_session,
    save_session,
)
from sft_provision_pod_mcp import (  # noqa: E402
    load_mcp_token,
    pod_exists,
    save_session as save_session_mcp,
    try_provision_pod,
    wait_ssh,
)

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


def wait_ssh_with_retry(session: dict, token: str) -> dict:
    pod_id = str(session.get("pod_id") or "")
    if session.get("ssh_host"):
        return session
    log(f"wait_ssh pod={pod_id} timeout_min={SSH_WAIT_MIN}")
    ssh_info = wait_ssh(token, pod_id, timeout_min=SSH_WAIT_MIN)
    session.update(ssh_info)
    save_session(session)
    log(f"ssh_ready {ssh_info['ssh_user']}@{ssh_info['ssh_host']}:{ssh_info['ssh_port']}")
    return session


def orchestrate_sft() -> bool:
    for attempt in range(1, ORCHESTRATE_RETRIES + 1):
        log(f"orchestrate attempt {attempt}/{ORCHESTRATE_RETRIES}")
        steps = [
            ("sft_verify_mount.ps1", []),
            ("sft_sync_to_pod.ps1", []),
            ("sft_inject_hf_token.ps1", []),
            ("sft_launch_train.ps1", []),
            ("sft_start_monitor.ps1", []),
        ]
        ok = True
        for script, args in steps:
            rc = run_ps1(script, *args)
            if rc != 0:
                log(f"FAILED {script} exit={rc}")
                ok = False
                break
        if ok:
            return True
        time.sleep(30)
    return False


def session_has_live_pod(session: dict, token: str) -> bool:
    pod_id = session.get("pod_id")
    if not pod_id:
        return False
    return pod_exists(token, str(pod_id))


def handle_live_pod(session: dict, token: str) -> str:
    pod_id = str(session.get("pod_id") or "")

    if session.get("ssh_host") and (training_running(session) or gpu_work_running(session)):
        log("WATCH_HANDOFF gpu work running — ensure monitor active")
        session["watch_status"] = "training_running"
        save_session(session)
        run_ps1("sft_start_monitor.ps1")
        return "training"

    try:
        session = wait_ssh_with_retry(session, token)
    except Exception as exc:
        log(f"ssh_wait_failed {exc}")
        if cleanup_idle_pod(session, token, force=False):
            log("deleted idle pod after ssh timeout window")
        return "waiting"

    log("pod live, no gpu work — orchestrating")
    if orchestrate_sft():
        session = load_session()
        session["watch_status"] = "training_launched"
        save_session(session)
        log("WATCH_OK training launched")
        return "training"

    # Orchestrate already retried internally; do not leave a GPU idle on credits.
    log("orchestrate failed — force-delete idle pod (no bill while waiting)")
    try:
        fetch_local_artifacts(partial=True)
    except Exception as exc:
        log(f"partial_fetch_warn {exc}")
    if cleanup_idle_pod(session, token, force=True):
        log(f"deleted idle pod {pod_id} after orchestrate failure")
    else:
        session["watch_status"] = "orchestrate_failed_no_pod"
        save_session(session)
        log("orchestrate failed and no pod to delete")
    return "waiting"


def watch_once(token: str) -> str:
    session = load_session()
    status = session.get("watch_status") or session.get("monitor_status") or ""

    # Stale "training_*" with no pod_id → resume capacity wait (do not exit as done).
    if status in ("training_launched", "training_running") and not session.get("pod_id"):
        log("stale training status without pod — resume capacity wait")
        session["watch_status"] = "waiting_capacity"
        save_session(session)
        status = "waiting_capacity"

    if status == "done_pod_deleted":
        log("WATCH_DONE prior run complete")
        return "done"

    if status in ("training_launched", "training_running"):
        if session_has_live_pod(session, token) and session.get("ssh_host") and (
            training_running(session) or gpu_work_running(session)
        ):
            run_ps1("sft_start_monitor.ps1")
            return "training"

    if session_has_live_pod(session, token):
        return handle_live_pod(session, token)

    pubkey = PUBKEY.read_text(encoding="utf-8").strip()
    log("no live pod — probing US-IL-1 4090/L40S + volume")
    result = try_provision_pod(token, pubkey)
    if not result:
        log("WATCH_WAIT no creatable GPU in US-IL-1 (volume 7hb931c5oe)")
        session["watch_status"] = "waiting_capacity"
        session["pod_id"] = None
        save_session(session)
        return "waiting"

    pod_id, meta = result
    meta["watch_status"] = "provisioned"
    meta["provisioned_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    save_session_mcp(meta)
    log(f"WATCH_PROVISIONED pod={pod_id} gpu={meta.get('gpu_type')} image={meta.get('image_name')}")

    session = load_session()
    try:
        session = wait_ssh_with_retry(session, token)
    except Exception as exc:
        log(f"ssh_wait_after_provision_failed {exc} — will retry next poll")
        session["watch_status"] = "ssh_pending"
        save_session(session)
        return "waiting"

    if orchestrate_sft():
        session = load_session()
        session["watch_status"] = "training_launched"
        save_session(session)
        log("WATCH_OK provisioned and training launched")
        return "training"

    log("WATCH_WARN provisioned but orchestrate failed — partial fetch, idle guard active")
    try:
        fetch_local_artifacts(partial=True)
    except Exception as exc:
        log(f"partial_fetch_warn {exc}")
    session = load_session()
    cleanup_idle_pod(session, token, force=False)
    return "waiting"


def main() -> None:
    log(
        f"sft_capacity_watch_start interval_sec={INTERVAL_SEC} "
        f"ssh_wait_min={SSH_WAIT_MIN} idle_delete_min={os.environ.get('SFT_IDLE_DELETE_MIN', '20')}"
    )
    token = load_mcp_token()
    while True:
        try:
            state = watch_once(token)
            if state in ("training", "done"):
                log(f"capacity_watch_exit state={state}")
                return
        except Exception as exc:
            log(f"capacity_watch_error {exc}")
        log(f"sleep {INTERVAL_SEC}s (no pod while waiting)")
        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    main()
