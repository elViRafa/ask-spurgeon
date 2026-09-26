#!/usr/bin/env python3
"""Local readiness for Vast S7 Phase B isolation C. No GPU rent."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import vast_cpt_s7_local_readiness as ready  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
CPT = REPO / "continued_pretrain"
EXPECT_B = "ddbbee3ac9ef7baf6cca21dcdb844d027d39f5f6a4b88ba10fcf8a43fa7c8214"
EXPECT_A = "06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432"
PIN_PURITAN = "e203eec759365aafb84be29c23b0dc8ff224d142aab9e14629154783e193184f"
PIN_CONFESSION = "14beb18998272fbcb09ee90571b44cb1b813ad5a0ce1dc2d0e15e9580768127e"
ADAPTER = (
    CPT
    / "kaggle"
    / "runpod_cpt_v3"
    / "vast_cpt_s7"
    / "fetch"
    / "theology_cpt_lora_s5best"
    / "theology_cpt_lora_s5best"
    / "adapter_model.safetensors"
)
TOP_LEVEL_A = (
    CPT
    / "kaggle"
    / "runpod_cpt_v3"
    / "vast_cpt_s7"
    / "fetch"
    / "theology_cpt_lora_s5best"
    / "adapter_model.safetensors"
)
HOLDOUTS_HF = CPT / "kaggle" / "a_output_v5" / "theology_holdouts"
PINNED = CPT / "data" / "holdouts_pinned_v3"
C_EVAL_PS1 = CPT / "scripts" / "vast_cpt_s7_c_eval.ps1"
DOC_SEP = "<|endoftext|>"


def parse_concat(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [d.strip() for d in text.split(DOC_SEP) if len(d.strip()) > 200]


def hf_holdout_texts(name: str) -> list[str]:
    from datasets import load_from_disk

    ds = load_from_disk(str(HOLDOUTS_HF / name))
    return [str(row["text"]).strip() for row in ds]


def main() -> int:
    errors: list[str] = []
    print("=== Vast S7 Phase B isolation C readiness (no rent) ===")

    if not ADAPTER.is_file():
        errors.append(f"missing nested Phase B s5best: {ADAPTER}")
    else:
        got = ready.sha256_file(ADAPTER).lower()
        print(f"phase_b_s5best_sha={got[:16]}... size_mb={ready.dir_mb(ADAPTER)}")
        if got != EXPECT_B:
            errors.append(f"Phase B s5best SHA mismatch got {got} want {EXPECT_B}")
        if got == EXPECT_A:
            errors.append("C-eval resolved to Phase A 06354dfc — use nested ddbbee3a")

    if TOP_LEVEL_A.is_file():
        top = ready.sha256_file(TOP_LEVEL_A).lower()
        print(f"top_level_s5best_sha={top[:16]}... (must stay Phase A)")
        if top != EXPECT_A:
            errors.append(f"top-level s5best drifted from Phase A got {top}")

    for name, expect in (
        ("puritan_holdout.txt", PIN_PURITAN),
        ("confession_holdout.txt", PIN_CONFESSION),
    ):
        pin = PINNED / name
        if not pin.is_file():
            errors.append(f"missing pin {name}")
            continue
        sha = ready.sha256_file(pin).lower()
        print(f"pin {name}={sha[:16]}...")
        if sha != expect:
            errors.append(f"pinned SHA mismatch {name} got {sha}")
        mix_ho = CPT / "data" / "mix_v5" / "holdouts" / name
        if mix_ho.is_file() and mix_ho.read_bytes() != pin.read_bytes():
            errors.append(f"mix_v5 holdout drifted from pin: {name}")

    for bucket in ("puritan", "confession"):
        dest = HOLDOUTS_HF / bucket / "dataset_info.json"
        if not dest.is_file():
            errors.append(f"missing HF holdout {bucket}")

    if HOLDOUTS_HF.is_dir() and (PINNED / "puritan_holdout.txt").is_file():
        try:
            for bucket, pin_name in (
                ("puritan", "puritan_holdout.txt"),
                ("confession", "confession_holdout.txt"),
            ):
                pinned_fps = {d[:200] for d in parse_concat(PINNED / pin_name)}
                hf_fps = {t[:200] for t in hf_holdout_texts(bucket)}
                extra = hf_fps - pinned_fps
                missing = pinned_fps - hf_fps
                print(f"hf_{bucket} docs={len(hf_fps)} pin_docs={len(pinned_fps)}")
                if extra or missing:
                    errors.append(
                        f"a_output_v5 {bucket} holdout does not match pinned v3 "
                        f"(extra={len(extra)} missing={len(missing)})"
                    )
        except Exception as exc:
            errors.append(f"HF holdout compare failed: {exc}")

    ps1 = C_EVAL_PS1.read_text(encoding="utf-8") if C_EVAL_PS1.is_file() else ""
    if EXPECT_B not in ps1:
        errors.append("vast_cpt_s7_c_eval.ps1 missing Phase B SHA ddbbee3a")
    if EXPECT_A in ps1 and "06354dfc" in ps1:
        # Phase A SHA may appear only as a "do not use" comment.
        assigned = any(
            line.strip().startswith("$ExpectedSha") and EXPECT_B in line
            for line in ps1.splitlines()
        )
        if not assigned:
            errors.append("vast_cpt_s7_c_eval.ps1 $ExpectedSha is not Phase B ddbbee3a")
    if "theology_cpt_lora_s5best\\theology_cpt_lora_s5best" not in ps1.replace("/", "\\"):
        errors.append("vast_cpt_s7_c_eval.ps1 AdapterDir is not the nested Phase B folder")
    if "vast_cpt_s7_c_phase_b" not in ps1 and "vast_cpt_s7_b_c" not in ps1:
        errors.append("C-eval results dir must be isolated from Phase A vast_cpt_s7_c")

    if errors:
        print("FAIL:")
        for e in errors:
            print(" -", e)
        return 1
    print("READY: Phase B isolation C artifacts OK (no rent)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
