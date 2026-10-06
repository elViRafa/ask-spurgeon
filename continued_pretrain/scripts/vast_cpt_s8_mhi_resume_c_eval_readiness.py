#!/usr/bin/env python3
"""Local readiness for S8 m_hi resume Isolation C. No GPU rent, no Hub push.

Pins flat ``theology_cpt_lora`` SHA 22698039 (checkpoint-2250). Refuses Phase A
06354dfc and other S5/S6/S7 adapters. Does not call vastai.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CPT = REPO / "continued_pretrain"
SCRIPTS = Path(__file__).resolve().parent

# m_hi resume best (in-train puritan 1.701 / Spurgeon 2.449). Not a Hub SHA.
EXPECT_RESUME = "2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207"
PHASE_A = "06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432"
# Scored adapter must not be an older train init or Hub production file.
FORBIDDEN: dict[str, str] = {
    PHASE_A: "Phase A Hub 06354dfc",
    "6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c": "S6 6aab",
    "ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303": "S5 ef4df3a3",
    "ddbbee3ac9ef7baf6cca21dcdb844d027d39f5f6a4b88ba10fcf8a43fa7c8214": "S7 Phase B ddbbee3a",
    "0289f1c9af70615ef4dca58b3e2d7dabc3eefef96c8bdf92bff0933689adeb55": "S7 replay 0289f1c9",
    "a70fded8aea1c9cb1a484e640e89137412519c28d95bdbfbf8d73ca2d2e42eac": "S7 P0 merge parent a70fded8",
}

ADAPTER_REL = (
    "kaggle/runpod_cpt_v3/vast_cpt_s8_mhi_resume/fetch/mhi_resume/theology_cpt_lora"
    "/adapter_model.safetensors"
)
# Same SHA. AdapterDir stays the flat theology_cpt_lora leaf, not this checkpoint.
CHECKPOINT_RELS = (
    "kaggle/runpod_cpt_v3/vast_cpt_s8_mhi_resume/fetch/mhi_resume/checkpoints"
    "/checkpoint-2250/adapter_model.safetensors",
    "kaggle/runpod_cpt_v3/vast_cpt_s8_mhi_resume/fetch/checkpoints"
    "/checkpoint-2250/adapter_model.safetensors",
)
HOLDOUT_REL = "kaggle/a_output_v6_p0/theology_holdouts"
REQUIRED_BUCKETS = ("spurgeon", "puritan", "confession", "general")
PS1_NAME = "vast_cpt_s8_mhi_resume_c_eval.ps1"
PS1_PATH = SCRIPTS / PS1_NAME
RESULTS_DIRNAME = "vast_cpt_s8_mhi_resume_c"
STACK_SH = "vast_remote_stack_isolation_c.sh"
S6_STACK_SH = "vast_remote_c_eval.sh"

_RENT_MARKERS = (
    "vastai",
    "Show-VastAccountSummary",
    "Invoke-Vastai",
    "vast_provision",
    "Find-VastCheapestOffer",
    "Get-VastSession",
    "scp ",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def sha_errors(got: str) -> list[str]:
    """Return reasons ``got`` is not the m_hi resume adapter."""
    lowered = (got or "").strip().lower()
    errors: list[str] = []
    if lowered != EXPECT_RESUME:
        errors.append(f"resume SHA mismatch got {lowered} want {EXPECT_RESUME}")
    for sha, label in FORBIDDEN.items():
        if lowered == sha:
            errors.append(f"refusing {label}")
    return errors


def _assignment_lines(text: str, name: str) -> list[str]:
    prefix = f"${name}".lower()
    found: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(prefix):
            found.append(stripped)
    return found


def _dry_head_and_tail(text: str) -> tuple[str, str, list[str]]:
    errors: list[str] = []
    lines = text.splitlines()
    go_idx = next((i for i, line in enumerate(lines) if "if (-not $Go)" in line), None)
    if go_idx is None:
        return "", text, ["ps1 missing dry gate: if (-not $Go)"]
    exit_idx = next(
        (i for i in range(go_idx, len(lines)) if lines[i].strip() == "exit 0"),
        None,
    )
    if exit_idx is None:
        return "", text, ["ps1 dry gate does not exit 0 before rent"]
    head = "\n".join(lines[: exit_idx + 1])
    tail = "\n".join(lines[exit_idx + 1 :])
    return head, tail, errors


def _code_without_comments(text: str) -> str:
    kept: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        kept.append(line)
    return "\n".join(kept)


def dry_head_errors(text: str) -> list[str]:
    """Default path is readiness only. Rent calls must sit below ``exit 0``."""
    head, tail, errors = _dry_head_and_tail(text)
    if errors:
        return errors
    if "[switch]$Go" not in text:
        errors.append("ps1 param missing [switch]$Go (dry must be the default)")
    if PS1_NAME.replace(".ps1", "_readiness.py") not in head and (
        "vast_cpt_s8_mhi_resume_c_eval_readiness.py" not in head
    ):
        errors.append("dry head must run vast_cpt_s8_mhi_resume_c_eval_readiness.py")
    code = _code_without_comments(head)
    for marker in _RENT_MARKERS:
        if marker in code:
            errors.append(f"dry head calls rent/marketplace before exit 0 ({marker.strip()})")
    if "vast_provision.ps1" not in tail:
        errors.append("-Go tail missing vast_provision.ps1")
    if "vast_destroy.ps1" not in tail:
        errors.append("-Go tail missing vast_destroy.ps1")
    if STACK_SH not in tail:
        errors.append(f"-Go tail must launch {STACK_SH}")
    if "KeepInstance" not in text:
        errors.append("ps1 missing -KeepInstance")
    return errors


def wiring_errors(text: str) -> list[str]:
    errors: list[str] = []
    expected = _assignment_lines(text, "ExpectedSha")
    if not any(EXPECT_RESUME in line for line in expected):
        errors.append("ps1 $ExpectedSha is not m_hi resume 22698039")
    for line in expected:
        for sha, label in FORBIDDEN.items():
            if sha in line.lower():
                errors.append(f"ps1 $ExpectedSha must not be {label}")
    adapters = _assignment_lines(text, "AdapterDir")
    flat = "vast_cpt_s8_mhi_resume\\fetch\\mhi_resume\\theology_cpt_lora"
    if not any(flat in line.replace("/", "\\") for line in adapters):
        errors.append("ps1 $AdapterDir is not flat mhi_resume/theology_cpt_lora")
    for line in adapters:
        normalized = line.replace("/", "\\").lower()
        if "checkpoint-2250" in normalized:
            errors.append("ps1 $AdapterDir must stay the flat leaf, not checkpoint-2250")
        if "vast_cpt_s6" in normalized or "vast_cpt_s7" in normalized:
            errors.append("ps1 $AdapterDir points at an S6/S7 fetch tree")
        if "theology_cpt_lora_s5best" in normalized:
            errors.append("ps1 $AdapterDir points at s5best, not m_hi resume")
    holdouts = _assignment_lines(text, "Holdouts")
    if not any(
        "a_output_v6_p0\\theology_holdouts" in line.replace("/", "\\") for line in holdouts
    ):
        errors.append("ps1 $Holdouts must be a_output_v6_p0")
    remotes = _assignment_lines(text, "RemoteSh")
    if not any(STACK_SH in line for line in remotes):
        errors.append(f"ps1 $RemoteSh must be {STACK_SH} (torch 2.8)")
    for line in remotes:
        if S6_STACK_SH in line:
            errors.append(f"ps1 $RemoteSh must not be {S6_STACK_SH} (torch 2.11)")
    results = [
        line
        for line in text.splitlines()
        if "VAST_LOCAL_RESULTS_DIR" in line or line.strip().startswith("$ResultsDir")
    ]
    if not any(RESULTS_DIRNAME in line for line in results):
        errors.append(f"ps1 results dir must be {RESULTS_DIRNAME}")
    for line in results:
        if "vast_cpt_s7" in line or "vast_cpt_s6" in line:
            errors.append("ps1 results dir points at an S6/S7 session")
    if "06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432" not in text:
        errors.append("ps1 must refuse Phase A 06354dfc when the file hash matches")
    errors.extend(dry_head_errors(text))
    return errors


def evaluate(
    *,
    adapter: Path,
    checkpoints: list[Path],
    holdout_root: Path,
    ps1_text: str,
) -> list[str]:
    errors: list[str] = []
    if not adapter.is_file():
        errors.append(f"missing flat resume adapter: {adapter}")
    else:
        got = sha256_file(adapter).lower()
        print(f"resume_lora_sha={got[:16]}...")
        errors.extend(sha_errors(got))

    present = [path for path in checkpoints if path.is_file()]
    if not present:
        errors.append(
            "missing checkpoint-2250 cross-check "
            "(fetch/mhi_resume/checkpoints/checkpoint-2250 or fetch/checkpoints/checkpoint-2250)"
        )
    for path in present:
        got = sha256_file(path).lower()
        print(f"checkpoint_sha={got[:16]}... path={path}")
        if got != EXPECT_RESUME:
            errors.append(f"checkpoint-2250 SHA mismatch got {got} want {EXPECT_RESUME}")
        if got == PHASE_A:
            errors.append("checkpoint-2250 is Phase A 06354dfc — refuse")

    for bucket in REQUIRED_BUCKETS:
        marker = holdout_root / bucket / "dataset_info.json"
        state = holdout_root / bucket / "state.json"
        if not marker.is_file() and not state.is_file():
            errors.append(f"missing a_output_v6_p0 holdout bucket {bucket}")

    errors.extend(wiring_errors(ps1_text))
    return errors


def main() -> int:
    print("=== S8 m_hi resume isolation C readiness (no rent, no vastai) ===")
    print(f"expect_sha={EXPECT_RESUME}")
    print("stack=Unsloth 2026.8.22 + torch 2.8 (vast_remote_stack_isolation_c.sh)")
    print("section5 puritan loss <= 1.6349; else keep Hub Phase A 06354dfc")
    adapter = CPT / ADAPTER_REL
    checkpoints = [CPT / rel for rel in CHECKPOINT_RELS]
    holdouts = CPT / HOLDOUT_REL
    ps1_text = PS1_PATH.read_text(encoding="utf-8") if PS1_PATH.is_file() else ""
    if not ps1_text:
        print("FAIL:")
        print(f" - missing {PS1_PATH}")
        return 1
    errors = evaluate(
        adapter=adapter,
        checkpoints=checkpoints,
        holdout_root=holdouts,
        ps1_text=ps1_text,
    )
    results = CPT / "kaggle" / "runpod_cpt_v3" / RESULTS_DIRNAME
    if not errors:
        results.mkdir(parents=True, exist_ok=True)
        print(f"results_dir={results}")
    if errors:
        print("FAIL:")
        for err in errors:
            print(" -", err)
        return 1
    print("READY: m_hi resume isolation C artifacts OK (no rent; -Go only after Rafael approves)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
