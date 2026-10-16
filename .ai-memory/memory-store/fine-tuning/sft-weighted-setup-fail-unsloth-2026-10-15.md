---
store_path: fine-tuning/sft-weighted-setup-fail-unsloth-2026-10-15
title: "Weighted SFT setup: skip unsloth on peft + fail watchdog"
summary: "`assert_pins` bare `import unsloth` under `set -e` → unsloth_zoo ImportError even with packages installed"
priority: high
tags: [sft, weighted, vast, peft, unsloth, watchdog]
schema_version: 1.3
last_updated: "2026-10-15T16:20:33-03:00"
evidence: ["commit:f82229b", fine_tuning/scripts/sft_remote_setup.sh, fine_tuning/scripts/sft_setup_fail_watchdog.sh, fine_tuning/scripts/vast_sft_s8_weighted_orchestrate.ps1]
---

# Weighted SFT setup fail fix (2026-10-15)

## Run3 failure
`assert_pins` bare `import unsloth` under `set -e` → unsloth_zoo ImportError even with packages installed. Setup exit 1; no smoke/train. Launcher without `-StartMonitor` left GPU idle ~30m. Image `/usr/local/lib/python3.11/dist-packages` (torchao cpython-310 .so) leaked into the train env.

## Fix on main (`f82229b`)
1. Install/import unsloth + unsloth_zoo only when `SFT_BACKEND=unsloth` (weighted uses peft).
2. Isolated venv: no system-site-packages, `PYTHONNOUSERSITE=1`, assert no image dist-packages on `sys.path`.
3. Verbose pip (no `-q`); LD/libcuda/torch.cuda diagnostics before first `unset LD_LIBRARY_PATH`; fail fast if nvidia-smi missing.
4. ERR trap → `SETUP_FAILED line=<n>` in `sft_setup.log`.
5. Detached `sft_setup_fail_watchdog.sh`: evidence then self-destroy on setup/smoke fail.
6. Orchestrator: try/catch → `Invoke-DestroyOnFail`; monitor breaks on `SETUP_FAILED` / `SMOKE_BEFORE_TRAIN_FAILED`; `-Go` implies `-StartMonitor`; `Start-Transcript`.

## Verify
- pytest env safeguards + monitor + weighted plan: 32 passed
- Dry: READY, DIRTY_OVERRIDES=(none)
- No GPU rented in this session

## Next
