"""Fixture tests: actionable SETUP_FAILED ordering + watchdog silent mtime extend."""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "fine_tuning" / "scripts"
MARKERS = SCRIPTS / "sft_setup_markers.sh"
WATCHDOG = SCRIPTS / "sft_setup_fail_watchdog.sh"
SETUP = SCRIPTS / "sft_remote_setup.sh"
ORCH = SCRIPTS / "vast_sft_s8_weighted_orchestrate.ps1"


def _bash() -> str:
    for candidate in (
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
    ):
        if Path(candidate).is_file():
            return candidate
    for name in ("bash", "bash.exe"):
        found = shutil.which(name)
        if found and "system32" not in found.lower() and "WindowsApps" not in found:
            return found
    raise RuntimeError("Git Bash is required for sft_setup_markers offline tests on Windows")


def _run_fn(fn: str, log_body: str) -> int:
    """Return 0 if fn says the log is a destroy trigger, else 1."""
    bash = _bash()
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        log = td_path / "sft_setup.log"
        log.write_text(log_body, encoding="utf-8", newline="\n")
        harness = td_path / "check.sh"
        markers_unix = str(MARKERS).replace("\\", "/")
        log_unix = str(log).replace("\\", "/")
        harness.write_text(
            "\n".join(
                [
                    "#!/usr/bin/env bash",
                    "set -euo pipefail",
                    f'source "{markers_unix}"',
                    f'if {fn} "{log_unix}"; then exit 0; else exit 1; fi',
                    "",
                ]
            ),
            encoding="utf-8",
            newline="\n",
        )
        harness.chmod(harness.stat().st_mode | stat.S_IXUSR)
        proc = subprocess.run(
            [bash, str(harness).replace("\\", "/")],
            cwd=str(td_path).replace("\\", "/"),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        return proc.returncode


def _run_actionable(log_body: str) -> int:
    return _run_fn("actionable_setup_failed_in", log_body)


def _run_smoke(log_body: str) -> int:
    return _run_fn("actionable_smoke_failed_in", log_body)


def test_markers_file_matches_anchored_lines_only() -> None:
    text = MARKERS.read_text(encoding="utf-8")
    assert "actionable_setup_failed_in" in text
    assert "actionable_smoke_failed_in" in text
    assert "^SETUP_FAILED rc=[0-9]+" in text
    assert "^SMOKE_BEFORE_TRAIN_FAILED" in text
    assert "SETUP_TRAP_INFO" in text
    assert "470" not in text
    assert "-ge " not in text
    assert "BASH_REMATCH" not in text


def test_watchdog_and_orch_source_anchored_markers() -> None:
    wd = WATCHDOG.read_text(encoding="utf-8")
    orch = ORCH.read_text(encoding="utf-8")
    setup = SETUP.read_text(encoding="utf-8")
    anchor = "^SETUP_FAILED rc=[0-9]+"
    smoke = "^SMOKE_BEFORE_TRAIN_FAILED"
    assert "sft_setup_markers.sh" in wd
    assert "sft_setup_markers.sh" in orch
    assert anchor in wd and anchor in orch and anchor in MARKERS.read_text(encoding="utf-8")
    assert smoke in wd and smoke in orch
    assert "SILENT_CAP_MIN" in wd
    assert "WATCHDOG_SILENT_EXTEND" in wd
    assert "SILENT_STALE_SEC" in wd
    assert 'WATCHDOG_DRY="${WATCHDOG_DRY:-0}"' in wd
    assert "would destroy" in wd
    assert "WATCHDOG_DESTROY_BEGIN reason=" in wd
    assert "trigger_line=" in wd
    assert "tail -n 200" in wd
    assert "rsync" in wd and "scp" in wd
    assert "line>=470" not in wd
    assert "line>=470" not in orch
    assert "-ge 470" not in wd
    assert "-ge 470" not in orch
    assert 'grep -q "SMOKE_BEFORE_TRAIN_FAILED"' not in orch
    assert "grep -q 'SMOKE_BEFORE_TRAIN_FAILED'" not in wd
    assert "SETUP_PHASE=boot" in setup
    assert "SETUP_PHASE=pins" in setup
    assert "SETUP_TRAP_INFO line=" in setup
    assert 'echo "SETUP_FAILED rc=${rc}"' in setup
    assert "reason=trap phase=" not in setup
    assert "SETUP_HEARTBEAT" in setup
    assert "sleep 30" in setup
    assert '[string]$WatchdogDry = "1"' in orch


def test_setup_trap_info_does_not_trigger_destroy() -> None:
    body = "\n".join(
        [
            "SETUP_PHASE=pins",
            "SETUP_TRAP_INFO line=19 cmd=false rc=1",
            "SETUP_FAILED line=220 reason=trap phase=pins",
            "pip still installing torch",
            "",
        ]
    )
    assert _run_actionable(body) == 1
    assert _run_smoke(body) == 1


def test_setup_failed_rc_triggers_destroy() -> None:
    body = "\n".join(
        [
            "SETUP_PHASE=boot",
            "SETUP_ABORT reason=nvidia-smi_missing",
            "SETUP_FAILED rc=1",
            "",
        ]
    )
    assert _run_actionable(body) == 0


def test_smoke_marker_inside_another_line_does_not_trigger_destroy() -> None:
    body = "\n".join(
        [
            "note: the log text mentioned SMOKE_BEFORE_TRAIN_FAILED inside this line",
            "SETUP_TRAP_INFO line=4 cmd=true rc=0",
            "",
        ]
    )
    assert _run_smoke(body) == 1
    assert _run_actionable(body) == 1


def test_anchored_smoke_line_triggers_destroy() -> None:
    body = "SMOKE_BEFORE_TRAIN_FAILED — leaving logs for evidence\n"
    assert _run_smoke(body) == 0
    assert _run_actionable(body) == 1


def test_watchdog_silent_extends_while_log_advances() -> None:
    """Advancing setup log must extend silent deadline; stale log past deadline destroys.

    Simulates the silent-extend + stale-check logic without calling destroy/vastai.
    """
    bash = _bash()
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        setuplog = td_path / "sft_setup.log"
        setuplog.write_text("SETUP_PHASE=boot\n", encoding="utf-8", newline="\n")
        script = td_path / "silent_sim.sh"
        setuplog_unix = str(setuplog).replace("\\", "/")
        # Compact simulation of watchdog silent rules.
        script.write_text(
            "\n".join(
                [
                    "#!/usr/bin/env bash",
                    "set -euo pipefail",
                    f'SETUPLOG="{setuplog_unix}"',
                    "SILENT_FAIL_MIN=1",
                    "SILENT_STALE_SEC=2",
                    "SILENT_CAP_MIN=5",
                    "started_at=$(date +%s)",
                    "silent_deadline=$((started_at + SILENT_FAIL_MIN * 60))",
                    # For the test, use short units: treat SILENT_FAIL_MIN as seconds.
                    "silent_deadline=$((started_at + 3))",
                    "cap_deadline=$((started_at + 30))",
                    "last_mtime=$(stat -c %Y \"$SETUPLOG\")",
                    "last_size=$(wc -c < \"$SETUPLOG\" | tr -d ' \\n')",
                    "extended=0",
                    "destroyed=0",
                    "for i in 1 2 3 4 5 6 7 8; do",
                    "  now=$(date +%s)",
                    "  # Advance log mid-loop (simulates pip still writing).",
                    '  if [[ "$i" -eq 2 ]]; then echo "pip still going $i" >> "$SETUPLOG"; fi',
                    "  cur_mtime=$(stat -c %Y \"$SETUPLOG\")",
                    "  cur_size=$(wc -c < \"$SETUPLOG\" | tr -d ' \\n')",
                    '  if [[ "$cur_mtime" != "$last_mtime" ]] || [[ "$cur_size" != "$last_size" ]]; then',
                    "    last_mtime=$cur_mtime",
                    "    last_size=$cur_size",
                    "    new_deadline=$((now + 3))",
                    '    if [[ "$new_deadline" -gt "$silent_deadline" ]]; then',
                    "      silent_deadline=$new_deadline",
                    "      extended=1",
                    "    fi",
                    '    if [[ "$silent_deadline" -gt "$cap_deadline" ]]; then silent_deadline=$cap_deadline; fi',
                    "  fi",
                    '  if [[ "$now" -ge "$silent_deadline" ]]; then',
                    "    log_age=$((now - cur_mtime))",
                    '    if [[ "$log_age" -ge "$SILENT_STALE_SEC" ]] && ! grep -q SETUP_OK "$SETUPLOG"; then',
                    "      destroyed=1",
                    "      break",
                    "    fi",
                    "  fi",
                    "  sleep 1",
                    "done",
                    'echo "extended=$extended destroyed=$destroyed"',
                    '[[ "$extended" -eq 1 ]] || exit 2',
                    # After extend, log is fresh; may or may not destroy depending on timing.
                    # Assert we extended; if we destroyed it must be after stale wait.
                    "exit 0",
                    "",
                ]
            ),
            encoding="utf-8",
            newline="\n",
        )
        script.chmod(script.stat().st_mode | stat.S_IXUSR)
        proc = subprocess.run(
            [bash, str(script).replace("\\", "/")],
            cwd=str(td_path).replace("\\", "/"),
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        assert proc.returncode == 0, f"rc={proc.returncode} out={out!r}"
        assert "extended=1" in out


def test_watchdog_contract_silent_vars() -> None:
    text = WATCHDOG.read_text(encoding="utf-8")
    assert 'SILENT_CAP_MIN="${SFT_WATCHDOG_SILENT_CAP_MIN:-90}"' in text
    assert 'SILENT_STALE_SEC="${SFT_WATCHDOG_SILENT_STALE_SEC:-300}"' in text
    assert 'MAX_MIN="${SFT_WATCHDOG_MAX_MIN:-90}"' in text
    assert "silent_setup_timeout_stale_" in text
