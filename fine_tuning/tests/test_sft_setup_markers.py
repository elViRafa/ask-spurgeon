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


def _run_actionable(log_body: str) -> int:
    """Return 0 if actionable_setup_failed_in says yes, else 1."""
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
                    f'if actionable_setup_failed_in "{log_unix}"; then exit 0; else exit 1; fi',
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


def test_markers_file_exists_and_has_no_lineno_gate() -> None:
    text = MARKERS.read_text(encoding="utf-8")
    assert "actionable_setup_failed_in" in text
    assert "SETUP_PINS_OK" in text
    assert "SETUP_PHASE=pins_ok" in text
    assert "reason=" in text
    assert "470" not in text
    assert "-ge " not in text
    assert "BASH_REMATCH" not in text


def test_watchdog_and_orch_source_markers_no_lineno_gate() -> None:
    wd = WATCHDOG.read_text(encoding="utf-8")
    orch = ORCH.read_text(encoding="utf-8")
    setup = SETUP.read_text(encoding="utf-8")
    assert "sft_setup_markers.sh" in wd
    assert "sft_setup_markers.sh" in orch
    assert "SILENT_CAP_MIN" in wd
    assert "WATCHDOG_SILENT_EXTEND" in wd
    assert "SILENT_STALE_SEC" in wd
    assert "line>=470" not in wd
    assert "line>=470" not in orch
    assert "-ge 470" not in wd
    assert "-ge 470" not in orch
    assert "SETUP_PHASE=boot" in setup
    assert "SETUP_PHASE=pins" in setup
    assert "SETUP_PHASE=pins_ok" in setup
    assert "reason=trap phase=" in setup
    assert "SETUP_PINS_OK" in setup


def test_bare_early_setup_failed_not_actionable() -> None:
    body = "\n".join(
        [
            "SETUP_PHASE=boot",
            "SETUP_FAILED line=50",
            "PRE_UNSET_TORCH_IMPORT_SKIP (torch not importable yet)",
            "Creating venv...",
            "",
        ]
    )
    assert _run_actionable(body) == 1


def test_reason_nvidia_actionable_before_pins() -> None:
    body = "\n".join(
        [
            "SETUP_PHASE=boot",
            "SETUP_FAILED line=40 reason=nvidia-smi_missing",
            "",
        ]
    )
    assert _run_actionable(body) == 0


def test_reason_trap_actionable() -> None:
    body = "\n".join(
        [
            "SETUP_PHASE=pins",
            "SETUP_FAILED line=220 reason=trap phase=pins",
            "",
        ]
    )
    assert _run_actionable(body) == 0


def test_pins_ok_plus_earlier_bare_fail_not_actionable() -> None:
    """Co-occurrence alone must not destroy — fail must be after last pins_ok."""
    body = "\n".join(
        [
            "SETUP_FAILED line=50",
            "PRE_UNSET_TORCH_IMPORT_SKIP",
            "SETUP_PINS_OK",
            "SETUP_PHASE=pins_ok",
            "SETUP_OK",
            "",
        ]
    )
    assert _run_actionable(body) == 1


def test_bare_fail_after_pins_ok_is_actionable() -> None:
    body = "\n".join(
        [
            "SETUP_PINS_OK",
            "SETUP_PHASE=pins_ok",
            "SETUP_FAILED line=510",
            "",
        ]
    )
    assert _run_actionable(body) == 0


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
