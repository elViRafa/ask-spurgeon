#!/usr/bin/env bash
# Smoke on official Unsloth image (no pip torch/unsloth reinstall).
set -euo pipefail
export CPT_WORK_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export PYTHONUNBUFFERED=1
mkdir -p "$HF_HOME" /workspace/unsloth_offload

if [[ -f /workspace/.sft_env ]]; then
  # shellcheck disable=SC1091
  source /workspace/.sft_env
fi
if [[ -n "${HF_TOKEN:-}" ]]; then
  export HUGGING_FACE_HUB_TOKEN="$HF_TOKEN"
fi

# Avoid system CUDA from base/host shadowing torch's bundled nvidia/*/lib.
unset LD_LIBRARY_PATH || true

# Prefer image python that already has unsloth.
PY=python3
if command -v python >/dev/null 2>&1; then
  if python -c "import unsloth" 2>/dev/null; then
    PY=python
  fi
fi
if ! "$PY" -c "import unsloth, torch; print('unsloth_ok', torch.__version__, torch.cuda.is_available())"; then
  echo "CPT_UNSLOTH_SMOKE_FAIL official_image_missing_unsloth"
  exit 2
fi

nvidia-smi || true
echo "OFFICIAL_IMAGE_OK - starting Unsloth CPT LoRA smoke with $PY"

set +e
"$PY" -u /workspace/smoke_vast_unsloth_cpt.py > /workspace/cpt_unsloth_smoke.log 2>&1
rc=$?
set -e
tail -n 80 /workspace/cpt_unsloth_smoke.log || true
if [[ $rc -eq 139 ]]; then
  echo "CPT_UNSLOTH_SMOKE_FAIL sigsegv_exit_139"
  exit 139
fi
if grep -q "CPT_UNSLOTH_SMOKE_PASS" /workspace/cpt_unsloth_smoke.log; then
  echo "REMOTE_SMOKE_PASS"
  exit 0
fi
echo "REMOTE_SMOKE_FAIL rc=$rc"
exit "$rc"
