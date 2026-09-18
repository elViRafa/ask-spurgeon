"""RunPod pod lifecycle helpers — idle detection, local artifact fetch, safe delete."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parents[1]
SESSION = REPO / "fine_tuning" / "kaggle" / "sft_session.json"
SSH_KEY = Path.home() / ".ssh" / "runpod_cpt"

# Delete pod if provisioned but no train/merge activity for this long (minutes).
IDLE_DELETE_MIN = int(__import__("os").environ.get("SFT_IDLE_DELETE_MIN", "20"))


def load_session() -> dict:
    if not SESSION.is_file():
        return {}
    return json.loads(SESSION.read_text(encoding="utf-8-sig"))


def save_session(data: dict) -> None:
    SESSION.parent.mkdir(parents=True, exist_ok=True)
    SESSION.write_text(json.dumps(data, indent=2), encoding="utf-8")


def ssh_cmd(session: dict, remote: str, timeout: int = 90) -> tuple[int, str]:
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
        f"ConnectTimeout={min(timeout, 60)}",
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
    return proc.returncode, ((proc.stdout or "") + (proc.stderr or "")).strip()


def gpu_work_running(session: dict) -> bool:
    """True if merge, train, eval, or install is actively using the GPU process slot."""
    checks = [
        "pgrep -af 'train_sft_sota.py' | grep -v pgrep || true",
        "pgrep -af 'merge_cpt_lora.py' | grep -v pgrep || true",
        "pgrep -af 'eval_sft_sota.py' | grep -v pgrep || true",
    ]
    for cmd in checks:
        _, out = ssh_cmd(session, cmd, timeout=30)
        for line in out.splitlines():
            if "pgrep" in line or "bash -c" in line:
                continue
            if any(x in line for x in ("train_sft_sota.py", "merge_cpt_lora.py", "eval_sft_sota.py")):
                return True
    return False


def pod_idle_minutes(session: dict) -> float | None:
    """Minutes since pod created if no gpu work running."""
    if gpu_work_running(session):
        return None
    created = session.get("created_at") or session.get("provisioned_at")
    if not created:
        return None
    try:
        from datetime import datetime

        start = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
        if start.tzinfo:
            start = start.replace(tzinfo=None)
        return (datetime.now() - start).total_seconds() / 60.0
    except Exception:
        return None


def run_ps1(name: str, *extra: str) -> int:
    ps1 = SCRIPT_DIR / name
    proc = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ps1),
            *extra,
        ],
        cwd=str(SCRIPT_DIR),
    )
    return proc.returncode


def fetch_local_artifacts(partial: bool = True) -> int:
    """Pull long-running GPU outputs to local disk (best-effort)."""
    fetch = SCRIPT_DIR / "sft_fetch_artifacts.ps1"
    if fetch.is_file():
        args = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(fetch),
        ]
        if partial:
            args.append("-PartialOnly")
        proc = subprocess.run(args, cwd=str(SCRIPT_DIR))
        return proc.returncode
    return run_ps1("sft_fetch_results.ps1")


def delete_pod(pod_id: str) -> None:
    sys.path.insert(0, str(SCRIPT_DIR))
    from sft_provision_pod_mcp import http_json, load_mcp_token

    token = load_mcp_token()
    status, payload = http_json(
        f"https://rest.runpod.io/v1/pods/{pod_id}", token, method="DELETE"
    )
    print(f"delete_pod {pod_id} status={status}", flush=True)
    if status not in (200, 201, 204):
        raise RuntimeError(f"Failed to delete pod {pod_id}: {payload}")


def pod_exists(token: str, pod_id: str) -> bool:
    sys.path.insert(0, str(SCRIPT_DIR))
    from sft_provision_pod_mcp import http_json

    status, payload = http_json(f"https://rest.runpod.io/v1/pods/{pod_id}", token)
    return status == 200 and isinstance(payload, dict)


def cleanup_idle_pod(session: dict, token: str, *, force: bool = False) -> bool:
    """Fetch partial artifacts and delete pod if idle too long. Returns True if deleted."""
    pod_id = str(session.get("pod_id") or "")
    if not pod_id or not pod_exists(token, pod_id):
        return False
    if gpu_work_running(session):
        return False
    idle = pod_idle_minutes(session)
    if not force and (idle is None or idle < IDLE_DELETE_MIN):
        return False
    print(f"idle_pod_cleanup pod={pod_id} idle_min={idle:.1f}", flush=True)
    try:
        fetch_local_artifacts(partial=True)
    except Exception as exc:
        print(f"fetch_before_delete_warn {exc}", flush=True)
    delete_pod(pod_id)
    session["pod_id"] = None
    session["watch_status"] = "idle_pod_deleted"
    session["idle_deleted_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_session(session)
    return True
