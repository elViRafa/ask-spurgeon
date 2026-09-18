"""Poll Vast GATE-0 every 15m: idle GPU → correct once or destroy.

Spend rules (Vast bills while RUNNING even if GPU idle):
- Process dead + finished → fetch + destroy
- Process dead + crash / unused → one relaunch attempt, then destroy on next idle poll
- Process alive but GPU ~0% and step not advancing for IDLE_STREAK polls → destroy
- Always destroy (not stop) — stopped storage still costs
"""
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
SESSION = REPO / "fine_tuning" / "kaggle" / "vast_sft_session.json"
SSH_KEY = Path.home() / ".ssh" / "runpod_cpt"

# Default 15 minutes — override with VAST_MONITOR_INTERVAL_SEC
INTERVAL_SEC = int(os.environ.get("VAST_MONITOR_INTERVAL_SEC", "900"))
MAX_WALL_HOURS = float(os.environ.get("VAST_MAX_WALL_HOURS", "10"))
SETUP_GRACE_MIN = float(os.environ.get("VAST_SETUP_GRACE_MIN", "70"))
# Consecutive idle polls before destroy (2 × 15m = 30m unused → kill)
IDLE_STREAK_LIMIT = int(os.environ.get("VAST_IDLE_STREAK_LIMIT", "2"))
IDLE_GPU_UTIL_MAX = float(os.environ.get("VAST_IDLE_GPU_UTIL_MAX", "5"))
IDLE_MEM_MIB_MAX = float(os.environ.get("VAST_IDLE_MEM_MIB_MAX", "2500"))


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
    _, out = ssh_cmd(session, "pgrep -af 'python3 -u /workspace/train_sft_sota.py' || true")
    for line in out.splitlines():
        if "train_sft_sota.py" in line and "pgrep" not in line and "bash -c" not in line:
            return True
    return False


def pipeline_running(session: dict) -> bool:
    if training_running(session):
        return True
    _, out = ssh_cmd(session, "pgrep -af 'bash /workspace/sft_remote_train.sh' || true")
    for line in out.splitlines():
        if "sft_remote_train.sh" in line and "pgrep" not in line:
            return True
    return False


def log_tail(session: dict, path: str, n: int = 40) -> str:
    _, out = ssh_cmd(session, f"tail -n {n} {path} 2>/dev/null || true")
    return out


def gpu_stats(session: dict) -> tuple[float | None, float | None]:
    """Return (util_percent, mem_used_mib) or (None, None) on failure."""
    rc, out = ssh_cmd(
        session,
        "nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits 2>/dev/null || true",
    )
    if rc != 0 or not out.strip():
        return None, None
    line = out.splitlines()[0].strip()
    # Drop banner lines
    for ln in out.splitlines():
        if "," in ln and not ln.lower().startswith("welcome"):
            line = ln.strip()
            break
    try:
        util_s, mem_s = [p.strip() for p in line.split(",")[:2]]
        return float(util_s), float(mem_s)
    except (ValueError, IndexError):
        return None, None


def parse_train_step(train_log: str) -> int | None:
    """Best-effort last 'N/408' style progress from tqdm / trainer logs."""
    step = None
    for m in re.finditer(r"(\d+)\s*/\s*(\d+)", train_log):
        cur, total = int(m.group(1)), int(m.group(2))
        if total >= 50:  # ignore tiny ratios
            step = cur
    return step


def training_crashed(train_log: str, running: bool) -> bool:
    """Only inspect sft_train.log — launch/setup Tracebacks must not destroy the pod."""
    if running:
        return False
    started = (
        "Total steps" in train_log
        or "SFTTrainer kwargs" in train_log
        or "PEFT path" in train_log
        or "SFT_BACKEND" in train_log
    )
    if not train_log.strip() or not started:
        return False
    tail = "\n".join(train_log.splitlines()[-30:])
    crash_markers = (
        "Traceback (most recent call last)",
        "RuntimeError:",
        "ImportError:",
        "CUDA out of memory",
        "torch.OutOfMemoryError",
        "SMOKE FAIL",
        "preflight FAIL",
        "merge FAIL",
        "SHA256 mismatch",
        "Segmentation fault",
        "exit 139",
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


def gpu_effectively_idle(util: float | None, mem: float | None) -> bool:
    if util is None or mem is None:
        return False  # unknown — do not destroy on missing metrics
    return util <= IDLE_GPU_UTIL_MAX and mem <= IDLE_MEM_MIB_MAX


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
    return run_ps1("vast_fetch.ps1", extra)


def delete_instance() -> None:
    rc = run_ps1("vast_destroy.ps1", ["-Force"])
    print("delete_instance exit", rc)
    if rc not in (0,):
        raise RuntimeError(f"vast_destroy.ps1 exit {rc}")


def combined_logs(session: dict) -> str:
    launch = log_tail(session, "/workspace/sft_launch.log", 80)
    train = log_tail(session, "/workspace/sft_train.log", 80)
    return launch + "\n" + train


def setup_failed(logs: str, wall_min: float, running: bool) -> bool:
    if running:
        return False
    if "SMOKE FAIL" in logs:
        return True
    if wall_min >= SETUP_GRACE_MIN and "SETUP_OK" not in logs and "SFT_BACKEND" not in logs:
        return True
    return False


def relaunch_train(session: dict) -> bool:
    """One corrective relaunch: PEFT + eval off, append to train log. Skip full setup."""
    remote = r"""
set -euo pipefail
source /workspace/.sft_env 2>/dev/null || true
export SFT_BACKEND=peft
export SFT_EVAL_STRATEGY=no
export SFT_PER_DEVICE_BATCH="${SFT_PER_DEVICE_BATCH:-1}"
export SFT_GRAD_ACCUM="${SFT_GRAD_ACCUM:-16}"
export SFT_MAX_SEQ_LENGTH="${SFT_MAX_SEQ_LENGTH:-2048}"
if pgrep -f 'python3 -u /workspace/train_sft_sota.py' >/dev/null 2>&1; then
  echo RELAUNCH_SKIP_ALREADY_RUNNING
  exit 0
fi
if [[ ! -f /workspace/theology_cpt_v2_merged_hf/config.json ]]; then
  echo RELAUNCH_FAIL_NO_MERGE
  exit 2
fi
echo "===== IDLE WATCH RELAUNCH $(date -u +%Y-%m-%dT%H:%M:%SZ) =====" >> /workspace/sft_train.log
nohup python3 -u /workspace/train_sft_sota.py >> /workspace/sft_train.log 2>&1 &
echo RELAUNCH_PID $!
sleep 5
pgrep -af 'python3 -u /workspace/train_sft_sota.py' || true
"""
    rc, out = ssh_cmd(session, remote, timeout=90)
    print("relaunch_out", out[:500], flush=True)
    return rc == 0 and ("RELAUNCH_PID" in out or "RELAUNCH_SKIP_ALREADY_RUNNING" in out)


def finish(session: dict, status: str, marker: str) -> None:
    session["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    session["monitor_status"] = status
    save_session(session)
    print(marker)


def main() -> None:
    session = load_session()
    inst = session.get("instance_id")
    wall = float(session.get("max_wall_hours") or MAX_WALL_HOURS)
    print(
        "monitor_start",
        inst,
        "interval_sec",
        INTERVAL_SEC,
        "idle_streak_limit",
        IDLE_STREAK_LIMIT,
        "max_wall_h",
        wall,
    )
    print(
        "ssh",
        f"{session.get('ssh_user', 'root')}@{session.get('ssh_host')}:{session.get('ssh_port', 22)}",
    )

    stale_not_running = 0
    idle_streak = 0
    last_step: int | None = None
    started = time.time()

    while True:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            session = load_session()
            wall_h = (time.time() - started) / 3600.0
            wall_min = (time.time() - started) / 60.0
            if wall > 0 and wall_h >= wall:
                print(f"[{ts}] max_wall {wall}h — fetch, destroy")
                fetch_results(partial=True)
                delete_instance()
                finish(session, "max_wall_destroyed", "MONITOR_DONE_MAX_WALL")
                return

            running = pipeline_running(session)
            train_run = training_running(session)
            util, mem = gpu_stats(session)
            train_log = log_tail(session, "/workspace/sft_train.log", 50)
            step = parse_train_step(train_log)
            logs = combined_logs(session)

            step_stuck = (
                last_step is not None
                and step is not None
                and step == last_step
                and train_run
            )
            idle_gpu = util is not None and util <= IDLE_GPU_UTIL_MAX
            # Dead process = unused. Alive but util~0 and same step for a full interval = stuck.
            unused = (not train_run and not running) or (train_run and idle_gpu and step_stuck)

            if running or train_run:
                if unused:
                    idle_streak += 1
                else:
                    idle_streak = 0
                    stale_not_running = 0
            else:
                stale_not_running += 1
                idle_streak += 1

            print(
                f"[{ts}] train={train_run} util={util} mem={mem} "
                f"step={step} idle_streak={idle_streak}/{IDLE_STREAK_LIMIT} "
                f"stale={stale_not_running} relaunch={session.get('idle_relaunch_count', 0)}",
                flush=True,
            )
            if logs:
                for line in logs.splitlines()[-3:]:
                    print("  ", line[:160], flush=True)

            if setup_failed(logs, wall_min, running or train_run):
                print(f"[{ts}] setup/smoke failed — fetch logs, destroy")
                fetch_results(partial=True)
                delete_instance()
                finish(session, "setup_failed_destroyed", "MONITOR_DONE_SETUP_FAIL")
                sys.exit(1)

            if training_finished(train_log, train_run, stale_not_running):
                print(f"[{ts}] training_done — fetch + destroy")
                fetch_results(partial=True)
                delete_instance()
                finish(session, "done_destroyed", "MONITOR_DONE")
                return

            # Corrective path: dead train (crash or unused) → one relaunch
            if (
                not train_run
                and wall_min >= 5
                and (
                    training_crashed(train_log, train_run)
                    or (idle_streak >= 1 and "SFT_BACKEND" in train_log)
                )
                and int(session.get("idle_relaunch_count") or 0) < 1
            ):
                print(f"[{ts}] unused/crash — attempting one corrective relaunch")
                ok = relaunch_train(session)
                session["idle_relaunch_count"] = int(session.get("idle_relaunch_count") or 0) + 1
                session["idle_relaunch_at"] = ts
                session["idle_relaunch_ok"] = ok
                save_session(session)
                idle_streak = 0
                stale_not_running = 0
                last_step = step
                time.sleep(INTERVAL_SEC)
                continue

            # Destroy if still unused across IDLE_STREAK_LIMIT polls
            if idle_streak >= IDLE_STREAK_LIMIT and wall_min >= 10:
                reason = "idle_gpu_unused" if unused else "stale_not_running"
                print(f"[{ts}] {reason} streak={idle_streak} — fetch + destroy (stop billing)")
                fetch_results(partial=True)
                delete_instance()
                finish(session, f"{reason}_destroyed", "MONITOR_DONE_IDLE")
                sys.exit(1)

            if training_crashed(train_log, train_run) and stale_not_running >= 2:
                if int(session.get("idle_relaunch_count") or 0) >= 1:
                    print(f"[{ts}] crash after relaunch — fetch + destroy")
                    fetch_results(partial=True)
                    delete_instance()
                    finish(session, "crashed_destroyed", "MONITOR_DONE_CRASH")
                    sys.exit(1)

            rc = fetch_results(partial=True)
            if rc != 0:
                print(f"[{ts}] fetch_warn exit={rc}", flush=True)

            last_step = step if step is not None else last_step
        except Exception as exc:
            print(f"[{ts}] monitor_error", exc, flush=True)

        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    main()
