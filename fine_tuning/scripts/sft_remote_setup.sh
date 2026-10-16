#!/usr/bin/env bash
# SFT GATE-0 / weighted: isolated Python env + Sep 6 package pins.
# Never mix image Python site-packages into the train venv (torchao cpython-310 .so).
# Prefer /workspace/sft_venv; fall back to Miniforge conda (vast-unsloth-conda-smoke-pass).
# Unsloth / unsloth_zoo install+import only when SFT_BACKEND=unsloth (weighted uses peft).
set -euo pipefail

SETUPLOG="${SFT_SETUP_LOG:-/workspace/sft_setup.log}"
mkdir -p "$(dirname "$SETUPLOG")" /workspace
touch "$SETUPLOG"

# Phase markers for watchdog/monitor (no $LINENO gating). Keep SETUP_PINS_OK / SETUP_OK.
SETUP_PHASE=boot
export SETUP_PHASE
echo "SETUP_PHASE=boot" | tee -a "$SETUPLOG"

on_setup_err() {
  local line="${1:-?}"
  local msg="SETUP_FAILED line=${line} reason=trap phase=${SETUP_PHASE:-unknown}"
  echo "$msg" | tee -a "$SETUPLOG"
}
trap 'on_setup_err $LINENO' ERR

export SFT_WORK_ROOT=/workspace
export HF_HOME=/workspace/hf_home
export PYTHONUNBUFFERED=1
export PYTHONFAULTHANDLER=1
export PYTHONNOUSERSITE=1
export DEBIAN_FRONTEND=noninteractive
unset PYTHONPATH || true

SFT_BACKEND="${SFT_BACKEND:-peft}"
SFT_BACKEND="$(echo "$SFT_BACKEND" | tr '[:upper:]' '[:lower:]')"
export SFT_BACKEND

# Diagnostics BEFORE first unset of LD_LIBRARY_PATH (operator evidence).
echo "=== CUDA / LD diagnostics (before unset) ===" | tee -a "$SETUPLOG"
echo "LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-<unset>}" | tee -a "$SETUPLOG"
if command -v ldconfig >/dev/null 2>&1; then
  ldconfig -p 2>/dev/null | grep -i libcuda | tee -a "$SETUPLOG" || echo "ldconfig: no libcuda line" | tee -a "$SETUPLOG"
else
  echo "ldconfig: not available" | tee -a "$SETUPLOG"
fi
if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "SETUP_FAILED line=${LINENO} reason=nvidia-smi_missing" | tee -a "$SETUPLOG"
  exit 1
fi
nvidia-smi -L 2>&1 | tee -a "$SETUPLOG" || {
  echo "SETUP_FAILED line=${LINENO} reason=nvidia-smi_failed" | tee -a "$SETUPLOG"
  exit 1
}
# Print torch.cuda.is_available() before unset (informational). Fail-fast on missing
# CUDA is nvidia-smi above; isolated-env assert_pins rechecks after pin install.
# Expected to fail before torch is installed — disable ERR trap (set +e alone does not).
# PRE_TORCH_PROBE_BEGIN
trap - ERR
set +e
python3 -c 'import torch; print("torch.cuda.is_available()", torch.cuda.is_available())' >>"$SETUPLOG" 2>&1
pre_torch_rc=$?
set -e
trap 'on_setup_err $LINENO' ERR
if [[ "$pre_torch_rc" -ne 0 ]]; then
  echo "PRE_UNSET_TORCH_IMPORT_SKIP (torch not importable yet; will recheck after pin install)" | tee -a "$SETUPLOG"
fi
# PRE_TORCH_PROBE_END

# Vast hosts often inject host CUDA libs that SIGSEGV under torch; drop them.
unset LD_LIBRARY_PATH || true

if [[ -f /workspace/.sft_env ]]; then
  # shellcheck disable=SC1091
  source /workspace/.sft_env
fi
# Re-assert after .sft_env (inject must not reintroduce LD_LIBRARY_PATH / PYTHONPATH).
unset LD_LIBRARY_PATH || true
unset PYTHONPATH || true
export PYTHONNOUSERSITE=1
export PYTHONFAULTHANDLER=1
SFT_BACKEND="${SFT_BACKEND:-peft}"
SFT_BACKEND="$(echo "$SFT_BACKEND" | tr '[:upper:]' '[:lower:]')"
export SFT_BACKEND

if [[ "${SFT_GPU_PROFILE:-}" == "a16" ]]; then
  export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
  export SFT_PER_DEVICE_BATCH="${SFT_PER_DEVICE_BATCH:-1}"
  export SFT_GRAD_ACCUM="${SFT_GRAD_ACCUM:-16}"
  echo "A16 profile: CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES} BATCH=${SFT_PER_DEVICE_BATCH} GRAD_ACCUM=${SFT_GRAD_ACCUM}"
elif [[ "${SFT_GPU_PROFILE:-}" == "4090" ]]; then
  export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
  export SFT_PER_DEVICE_BATCH="${SFT_PER_DEVICE_BATCH:-2}"
  export SFT_GRAD_ACCUM="${SFT_GRAD_ACCUM:-8}"
  echo "4090 profile: CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES} BATCH=${SFT_PER_DEVICE_BATCH} GRAD_ACCUM=${SFT_GRAD_ACCUM}"
fi

CONSTRAINTS="${SFT_CONSTRAINTS_FILE:-/workspace/sft_gate0_sep6_constraints.txt}"
VENV_DIR=/workspace/sft_venv
CONDA_ROOT=/workspace/miniforge3
CONDA_ENV=sft_train
UNSLOTH_GIT_PIN="git+https://github.com/unslothai/unsloth.git@6816025b41fe30df9cfe0eafef7a37f17eb31ab4"
TORCH_INDEX="https://download.pytorch.org/whl/cu126"

wait_apt() {
  local i=0
  while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 \
     || fuser /var/lib/apt/lists/lock >/dev/null 2>&1 \
     || fuser /var/lib/dpkg/lock >/dev/null 2>&1; do
    i=$((i + 1))
    if [[ $i -gt 120 ]]; then
      echo "apt lock still held after ~10m"
      return 1
    fi
    sleep 5
  done
}

ensure_unzip() {
  if command -v unzip >/dev/null 2>&1; then
    return 0
  fi
  echo "Installing unzip (missing on CUDA base images)"
  wait_apt
  apt-get update -qq
  wait_apt
  apt-get install -y -qq unzip
}

ensure_python311_system() {
  if command -v python3.11 >/dev/null 2>&1; then
    return 0
  fi
  echo "Bootstrapping system python3.11 for venv creation"
  wait_apt
  apt-get update -qq
  wait_apt
  if ! apt-get install -y -qq python3.11 python3.11-venv python3.11-dev; then
    echo "python3.11 not in default apt — trying deadsnakes"
    wait_apt
    apt-get install -y -qq software-properties-common curl ca-certificates
    wait_apt
    add-apt-repository -y ppa:deadsnakes/ppa
    wait_apt
    apt-get update -qq
    wait_apt
    apt-get install -y -qq python3.11 python3.11-venv python3.11-dev
  fi
}

install_miniforge() {
  if [[ -x "$CONDA_ROOT/bin/conda" ]]; then
    echo "Miniforge already present"
    return 0
  fi
  echo "Installing Miniforge to $CONDA_ROOT (conda fallback)"
  curl -fsSL https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -o /tmp/miniforge.sh
  bash /tmp/miniforge.sh -b -u -p "$CONDA_ROOT"
  rm -f /tmp/miniforge.sh
}

write_constraints_if_missing() {
  if [[ -f "$CONSTRAINTS" ]]; then
    echo "CONSTRAINTS_FILE=$CONSTRAINTS"
    return 0
  fi
  echo "Writing default Sep 6 constraints to $CONSTRAINTS"
  cat > "$CONSTRAINTS" <<'EOF'
torch==2.11.0+cu126
torchvision==0.26.0+cu126
torchaudio==2.11.0+cu126
torchao==0.18.0
transformers==5.5.0
peft==0.20.0
trl==0.24.0
accelerate==1.14.0
bitsandbytes==0.50.2
triton==3.6.0
unsloth_zoo==2026.9.1
datasets==4.3.0
huggingface_hub==1.30.0
safetensors==0.8.0
tokenizers==0.22.2
sentencepiece==0.2.2
protobuf==7.36.1
numpy==2.4.6
EOF
}

force_venv_no_system_site() {
  local cfg="$1/pyvenv.cfg"
  if [[ ! -f "$cfg" ]]; then
    return 0
  fi
  if grep -qiE 'include-system-site-packages\s*=\s*true' "$cfg"; then
    echo "REFUSING contaminated venv (include-system-site-packages=true); recreating"
    return 1
  fi
  # Normalize to false even if missing/odd whitespace.
  if grep -qiE 'include-system-site-packages' "$cfg"; then
    sed -i 's/[Ii]nclude-system-site-packages.*/include-system-site-packages = false/' "$cfg"
  else
    echo "include-system-site-packages = false" >> "$cfg"
  fi
  return 0
}

pip_install_pinned() {
  local py="$1"
  SETUP_PHASE=pins
  export SETUP_PHASE
  echo "SETUP_PHASE=pins" | tee -a "$SETUPLOG"
  echo "Upgrading pip in isolated env (verbose; no -q)"
  "$py" -m pip install --upgrade pip
  echo "Installing torch 2.11.0+cu126 into isolated env (cu126 index)"
  "$py" -m pip install --index-url "$TORCH_INDEX" \
    "torch==2.11.0+cu126" "torchvision==0.26.0+cu126" "torchaudio==2.11.0+cu126"
  echo "Installing Sep 6 train stack under constraints (no flash-linear-attention / causal-conv1d)"
  local pkgs=(
    torchao==0.18.0
    transformers==5.5.0
    peft==0.20.0
    trl==0.24.0
    accelerate==1.14.0
    bitsandbytes==0.50.2
    triton==3.6.0
    datasets==4.3.0
    huggingface_hub==1.30.0
    safetensors==0.8.0
    tokenizers==0.22.2
    sentencepiece==0.2.2
  )
  if [[ "$SFT_BACKEND" == "unsloth" ]]; then
    pkgs+=(unsloth_zoo==2026.9.1)
  else
    echo "SFT_BACKEND=${SFT_BACKEND}: skipping unsloth_zoo install"
  fi
  "$py" -m pip install -c "$CONSTRAINTS" "${pkgs[@]}"
  if [[ "$SFT_BACKEND" == "unsloth" ]]; then
    echo "Installing unsloth git pin 6816025b"
    "$py" -m pip install -c "$CONSTRAINTS" "unsloth[colab-new] @ ${UNSLOTH_GIT_PIN}"
  else
    echo "SFT_BACKEND=${SFT_BACKEND}: skipping unsloth install"
  fi
  # Refuse known-bad extras if a transitive dep pulled them.
  "$py" - <<'PY'
import importlib.util
bad = []
for name in ("flash_linear_attention", "causal_conv1d"):
    if importlib.util.find_spec(name) is not None:
        bad.append(name)
if bad:
    raise SystemExit(f"REFUSING forbidden packages in env: {bad}")
print("FORBIDDEN_PACKAGES_ABSENT ok")
PY
}

assert_no_image_dist_packages() {
  local py="$1"
  "$py" - <<'PY'
import sys
bad = []
for p in sys.path:
    norm = (p or "").replace("\\", "/")
    if not norm:
        continue
    if "/dist-packages" not in norm and "/site-packages" not in norm:
        continue
    # Allow only packages inside our isolated env roots.
    if "/sft_venv/" in norm or "/envs/sft_train/" in norm or "/miniforge3/envs/" in norm:
        continue
    # Image / system leakage (Vast CUDA images ship /usr/local/lib/python3.11/dist-packages).
    if (
        norm.startswith("/usr/local/")
        or norm.startswith("/usr/lib/")
        or "/python3.10/" in norm
        or "cpython-310" in norm
    ):
        bad.append(norm)
if bad:
    raise SystemExit(f"REFUSING image/system site-packages on sys.path: {bad}")
print("SYS_PATH_ISOLATED_OK", sys.executable)
print("sys.path:", sys.path)
PY
}

assert_pins() {
  local py="$1"
  echo "=== PIN ASSERT (backend=${SFT_BACKEND}) ==="
  SFT_BACKEND="$SFT_BACKEND" "$py" - <<'PY'
import importlib
import os
import sys

backend = (os.environ.get("SFT_BACKEND") or "peft").strip().lower()

def ver(mod):
    m = importlib.import_module(mod)
    return getattr(m, "__version__", "?")

checks = {
    "torch": "2.11.0+cu126",
    "transformers": "5.5.0",
    "peft": "0.20.0",
    "trl": "0.24.0",
    "accelerate": "1.14.0",
    "bitsandbytes": "0.50.2",
    "triton": "3.6.0",
}
if backend == "unsloth":
    checks["unsloth_zoo"] = "2026.9.1"

failed = []
for mod, want in checks.items():
    got = ver(mod)
    ok = got == want or got.startswith(want.split("+")[0])
    # torch must carry cu126 tag
    if mod == "torch":
        ok = got == want
    print(f"  {mod}: {got} (want {want}) {'OK' if ok else 'FAIL'}")
    if not ok:
        failed.append((mod, got, want))

import torch
print("  torch.cuda:", torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "n/a")
if not torch.cuda.is_available():
    raise SystemExit("PIN ASSERT FAIL: torch.cuda.is_available() is False")
print("  python:", sys.version.split()[0], "exe:", sys.executable)
assert (3, 11) <= sys.version_info[:2] <= (3, 13), f"Need Python 3.11–3.13, got {sys.version}"
assert sys.version_info[:2] != (3, 14), "Python 3.14 is not supported"
# Refuse site-packages pollution from image 3.10
exe = sys.executable.replace("\\", "/")
assert "/sft_venv/" in exe or "/envs/sft_train/" in exe or "/miniforge3/envs/" in exe, (
    f"REFUSING non-isolated python: {sys.executable}"
)

# Refuse image dist-packages on sys.path (torchao cpython-310 leak class).
bad_path = []
for p in sys.path:
    norm = (p or "").replace("\\", "/")
    if not norm:
        continue
    if "/dist-packages" not in norm and "/site-packages" not in norm:
        continue
    if "/sft_venv/" in norm or "/envs/sft_train/" in norm or "/miniforge3/envs/" in norm:
        continue
    if (
        norm.startswith("/usr/local/")
        or norm.startswith("/usr/lib/")
        or "/python3.10/" in norm
    ):
        bad_path.append(norm)
if bad_path:
    raise SystemExit(f"REFUSING image/system site-packages on sys.path: {bad_path}")
print("  sys.path: no image dist-packages OK")

# torchao must not be a 3.10 extension under 3.11
try:
    import torchao  # noqa: F401
    import pathlib
    root = pathlib.Path(torchao.__file__).resolve().parent
    bad_sos = list(root.rglob("*cpython-310*.so"))
    if bad_sos:
        raise SystemExit(f"torchao has cpython-310 .so under this interpreter: {bad_sos[:3]}")
    ta_path = str(root).replace("\\", "/")
    if "/usr/local/" in ta_path or "/usr/lib/" in ta_path:
        raise SystemExit(f"torchao loaded from image path: {ta_path}")
    print("  torchao: no cpython-310 .so OK", ta_path)
except ImportError:
    print("  torchao: not imported (optional)")

if backend == "unsloth":
    import unsloth
    print("  unsloth:", getattr(unsloth, "__version__", "ok"))
else:
    print(f"  unsloth: skipped (SFT_BACKEND={backend})")

if failed:
    raise SystemExit(f"PIN ASSERT FAIL: {failed}")
print("PIN_ASSERT_OK")
PY
}

write_env_hooks() {
  local py_bin="$1"
  local bin_dir
  bin_dir="$(dirname "$py_bin")"
  {
    echo "# written by sft_remote_setup.sh — isolated train env"
    echo "unset LD_LIBRARY_PATH || true"
    echo "unset PYTHONPATH || true"
    echo "export PYTHONNOUSERSITE=1"
    echo "export PYTHONFAULTHANDLER=1"
    echo "export PATH=\"${bin_dir}:\$PATH\""
    echo "export SFT_PYTHON=\"${py_bin}\""
    echo "export VIRTUAL_ENV=\"${VENV_DIR}\""
  } > /workspace/.sft_isolated_env
  # Prepend to .sft_env so later injects still see PATH; keep HF token file intact.
  if [[ -f /workspace/.sft_env ]]; then
    if ! grep -q "sft_isolated_env" /workspace/.sft_env 2>/dev/null; then
      {
        echo ""
        echo "# isolated SFT env (do not mix system site-packages)"
        echo "source /workspace/.sft_isolated_env"
      } >> /workspace/.sft_env
    fi
  else
    cp /workspace/.sft_isolated_env /workspace/.sft_env
  fi
  ln -sfn "$py_bin" /workspace/sft_python
  echo "SFT_PYTHON=$py_bin"
}

ensure_isolated_env() {
  write_constraints_if_missing
  ensure_python311_system

  local py=""
  local recreate=0
  if [[ -x "$VENV_DIR/bin/python" ]]; then
    if force_venv_no_system_site "$VENV_DIR"; then
      echo "Reusing existing venv $VENV_DIR"
      py="$VENV_DIR/bin/python"
    else
      recreate=1
    fi
  else
    recreate=1
  fi

  if [[ "$recreate" == "1" ]]; then
    echo "Creating isolated venv at $VENV_DIR (python3.11, no system-site-packages)"
    rm -rf "$VENV_DIR"
    # Explicit: never pass --system-site-packages.
    python3.11 -m venv --clear "$VENV_DIR"
    force_venv_no_system_site "$VENV_DIR" || true
    py="$VENV_DIR/bin/python"
  fi

  # Verify venv python is 3.11–3.13 and not using system site-packages for torch.
  if ! "$py" - <<'PY'
import sys
assert (3, 11) <= sys.version_info[:2] <= (3, 13)
print("venv_python", sys.version.split()[0], sys.executable)
PY
  then
    echo "venv broken — falling back to Miniforge conda env"
    install_miniforge
    # shellcheck disable=SC1091
    source "$CONDA_ROOT/etc/profile.d/conda.sh"
    conda config --set always_yes yes
    if ! conda env list | grep -qE "^${CONDA_ENV}\\s"; then
      conda create -y -n "$CONDA_ENV" python=3.11
    fi
    conda activate "$CONDA_ENV"
    unset LD_LIBRARY_PATH || true
    unset PYTHONPATH || true
    export PYTHONNOUSERSITE=1
    py="$CONDA_ROOT/envs/$CONDA_ENV/bin/python"
    VENV_DIR="$CONDA_ROOT/envs/$CONDA_ENV"
  fi

  assert_no_image_dist_packages "$py"

  local need_install=0
  # Fresh venvs fail these imports — `||` is enough for set -e, but clear ERR trap
  # so a future edit that drops `||` cannot emit a false SETUP_FAILED.
  trap - ERR
  if [[ "$SFT_BACKEND" == "unsloth" ]]; then
    "$py" - <<'PY' || need_install=1
import torch, transformers, peft, trl, accelerate, bitsandbytes, triton, unsloth_zoo
assert torch.__version__ == "2.11.0+cu126"
assert transformers.__version__ == "5.5.0"
assert peft.__version__ == "0.20.0"
assert trl.__version__ == "0.24.0"
assert accelerate.__version__ == "1.14.0"
print("pins_already_ok")
PY
  else
    "$py" - <<'PY' || need_install=1
import torch, transformers, peft, trl, accelerate, bitsandbytes, triton
assert torch.__version__ == "2.11.0+cu126"
assert transformers.__version__ == "5.5.0"
assert peft.__version__ == "0.20.0"
assert trl.__version__ == "0.24.0"
assert accelerate.__version__ == "1.14.0"
print("pins_already_ok")
PY
  fi
  trap 'on_setup_err $LINENO' ERR
  if [[ "$need_install" == "1" ]]; then
    pip_install_pinned "$py"
  fi

  echo "LD_LIBRARY_PATH_BEFORE_PIN_UNSET=${LD_LIBRARY_PATH:-<unset>}"
  unset LD_LIBRARY_PATH || true
  assert_no_image_dist_packages "$py"
  assert_pins "$py"
  SETUP_PHASE=pins_ok
  export SETUP_PHASE
  echo "SETUP_PINS_OK" | tee -a "$SETUPLOG"
  echo "SETUP_PHASE=pins_ok" | tee -a "$SETUPLOG"
  "$py" -m pip freeze > /workspace/sft_pip_freeze.txt
  echo "Wrote /workspace/sft_pip_freeze.txt ($(wc -l < /workspace/sft_pip_freeze.txt) lines)"
  write_env_hooks "$py"

  if [[ "$SFT_BACKEND" == "unsloth" ]]; then
    SFT_BACKEND="$SFT_BACKEND" "$py" - <<'PY'
import os
import torch
from torch.nn.functional import ScalingType
from trl import SFTConfig, SFTTrainer
import unsloth

if not torch.cuda.is_available():
    raise SystemExit("SMOKE FAIL: CUDA not available")
major, _ = torch.cuda.get_device_capability(0)
if major < 8:
    raise SystemExit(f"SMOKE FAIL: need Ampere+ sm_80, got {torch.cuda.get_device_capability(0)}")
print(
    "SMOKE_OK",
    "backend", os.environ.get("SFT_BACKEND"),
    "torch", torch.__version__,
    "cuda", torch.cuda.get_device_name(0),
    "cap", torch.cuda.get_device_capability(0),
    "ScalingType", ScalingType,
)
print("trl", SFTConfig.__name__, SFTTrainer.__name__)
print("unsloth", getattr(unsloth, "__version__", "ok"))
PY
  else
    SFT_BACKEND="$SFT_BACKEND" "$py" - <<'PY'
import os
import torch
from torch.nn.functional import ScalingType
from trl import SFTConfig, SFTTrainer

if not torch.cuda.is_available():
    raise SystemExit("SMOKE FAIL: CUDA not available")
major, _ = torch.cuda.get_device_capability(0)
if major < 8:
    raise SystemExit(f"SMOKE FAIL: need Ampere+ sm_80, got {torch.cuda.get_device_capability(0)}")
print(
    "SMOKE_OK",
    "backend", os.environ.get("SFT_BACKEND"),
    "torch", torch.__version__,
    "cuda", torch.cuda.get_device_name(0),
    "cap", torch.cuda.get_device_capability(0),
    "ScalingType", ScalingType,
)
print("trl", SFTConfig.__name__, SFTTrainer.__name__)
print("unsloth skipped (SFT_BACKEND=%s)" % os.environ.get("SFT_BACKEND"))
PY
  fi
}

ensure_unzip
mkdir -p /kaggle/input/datasets/spurgeon-qa-mix-v1 /kaggle/working/hf_home /kaggle/working/unsloth_offload /workspace/sft_nb "$HF_HOME"

if [[ -f /workspace/spurgeon-qa-mix-v1.zip ]]; then
  unzip -o /workspace/spurgeon-qa-mix-v1.zip -d /kaggle/input/datasets/spurgeon-qa-mix-v1
fi
ls -la /kaggle/input/datasets/spurgeon-qa-mix-v1 || true

# Prefer constraints shipped with sparse sync.
if [[ -f /workspace/sft_gate0_sep6_constraints.txt ]]; then
  CONSTRAINTS=/workspace/sft_gate0_sep6_constraints.txt
elif [[ -f /workspace/ask-spurgeon-src/fine_tuning/scripts/sft_gate0_sep6_constraints.txt ]]; then
  cp /workspace/ask-spurgeon-src/fine_tuning/scripts/sft_gate0_sep6_constraints.txt /workspace/sft_gate0_sep6_constraints.txt
  CONSTRAINTS=/workspace/sft_gate0_sep6_constraints.txt
fi

ensure_isolated_env
unset LD_LIBRARY_PATH || true
SETUP_PHASE=ok
export SETUP_PHASE
echo "SETUP_OK" | tee -a "$SETUPLOG"
echo "SETUP_PHASE=ok" | tee -a "$SETUPLOG"
