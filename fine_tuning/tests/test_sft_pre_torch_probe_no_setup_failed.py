"""Offline: pre-torch probe must not emit SETUP_FAILED when python3 exits 1."""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SETUP = REPO / "fine_tuning" / "scripts" / "sft_remote_setup.sh"
WATCHDOG = REPO / "fine_tuning" / "scripts" / "sft_setup_fail_watchdog.sh"
ORCH = REPO / "fine_tuning" / "scripts" / "vast_sft_s8_weighted_orchestrate.ps1"


def _bash() -> str:
    # Prefer Git Bash on Windows — system32\bash.EXE is WSL and mangles Win paths.
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
    raise RuntimeError("Git Bash is required for pre-torch probe offline test on Windows")


def _extract_probe_section(setup_text: str) -> str:
    begin = "# PRE_TORCH_PROBE_BEGIN"
    end = "# PRE_TORCH_PROBE_END"
    assert begin in setup_text, "missing PRE_TORCH_PROBE_BEGIN marker"
    assert end in setup_text, "missing PRE_TORCH_PROBE_END marker"
    body = setup_text.split(begin, 1)[1].split(end, 1)[0]
    return body.strip("\n")


def test_setup_probe_disables_err_trap_and_captures_python_rc() -> None:
    text = SETUP.read_text(encoding="utf-8")
    probe = _extract_probe_section(text)
    assert "trap - ERR" in probe
    assert "trap 'on_setup_err $LINENO' ERR" in probe
    assert "pre_torch_rc=$?" in probe
    # Must not pipe the python probe through tee (that captures tee's status).
    py_lines = [ln for ln in probe.splitlines() if "python3 -c" in ln]
    assert py_lines, "probe must invoke python3 -c"
    assert all("| tee" not in ln for ln in py_lines)
    assert "PIPESTATUS" not in probe or "pre_torch_rc=${PIPESTATUS[0]}" in probe
    assert "SETUP_PINS_OK" in text
    assert "on_setup_err" in text


def test_watchdog_and_monitor_gate_setup_failed_until_pins_ok() -> None:
    wd = WATCHDOG.read_text(encoding="utf-8")
    orch = ORCH.read_text(encoding="utf-8")
    assert "actionable_setup_failed_in" in wd
    assert "sft_setup_markers.sh" in wd
    assert "SETUP_PINS_OK" in wd
    assert "reason=" in wd
    assert "-ge 470" not in wd
    assert "SETUP_PINS_OK" in orch
    assert "actionable_setup_failed_in" in orch
    assert "sft_setup_markers.sh" in orch
    assert "-ge 470" not in orch
    assert "evidence saved (incomplete)" not in orch
    # Success message only when requiredOk.
    assert 'Write-Host "evidence saved: $evDir"' in orch


def test_pre_torch_probe_fake_python_exits_1_no_setup_failed() -> None:
    """Run the script's probe block with a python3 that exits 1; no SETUP_FAILED."""
    setup_text = SETUP.read_text(encoding="utf-8")
    probe = _extract_probe_section(setup_text)
    bash = _bash()

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        setuplog = td_path / "sft_setup.log"
        bin_dir = td_path / "bin"
        bin_dir.mkdir()
        fake_py = bin_dir / "python3"
        # Portable stub: always fail (simulates missing torch).
        fake_py.write_text(
            "#!/usr/bin/env bash\necho 'ModuleNotFoundError: No module named torch' >&2\nexit 1\n",
            encoding="utf-8",
            newline="\n",
        )
        fake_py.chmod(fake_py.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        harness = td_path / "run_probe.sh"
        # Resolve paths inside bash so Git Bash on Windows finds the fake python3.
        harness.write_text(
            "\n".join(
                [
                    "#!/usr/bin/env bash",
                    "set -euo pipefail",
                    'ROOT="$(cd "$(dirname "$0")" && pwd)"',
                    'export PATH="$ROOT/bin:$PATH"',
                    'SETUPLOG="$ROOT/sft_setup.log"',
                    "touch \"$SETUPLOG\"",
                    "on_setup_err() {",
                    '  local line="${1:-?}"',
                    '  echo "SETUP_FAILED line=${line}" | tee -a "$SETUPLOG"',
                    "}",
                    "trap 'on_setup_err $LINENO' ERR",
                    "# --- probe from sft_remote_setup.sh ---",
                    probe,
                    'echo "PROBE_HARNESS_DONE rc=${pre_torch_rc:-unset}" | tee -a "$SETUPLOG"',
                    "",
                ]
            ),
            encoding="utf-8",
            newline="\n",
        )

        # Git Bash accepts forward-slash Windows paths; WSL does not.
        harness_arg = str(harness).replace("\\", "/")
        cwd_arg = str(td_path).replace("\\", "/")
        proc = subprocess.run(
            [bash, harness_arg],
            cwd=cwd_arg,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        log = setuplog.read_text(encoding="utf-8") if setuplog.is_file() else ""
        combined = (proc.stdout or "") + (proc.stderr or "") + log

        assert proc.returncode == 0, (
            f"probe harness should succeed; rc={proc.returncode}\n"
            f"stdout={proc.stdout!r}\nstderr={proc.stderr!r}\nlog={log!r}"
        )
        assert "SETUP_FAILED" not in log, f"SETUP_FAILED leaked into log:\n{log}"
        assert "SETUP_FAILED" not in combined, f"SETUP_FAILED in output:\n{combined}"
        assert "PRE_UNSET_TORCH_IMPORT_SKIP" in log
        assert "PROBE_HARNESS_DONE rc=1" in log
