# Next job — RunPod Unsloth weighted SFT on S8 merged CPT

Same training contract as [NEXT_SFT_S8_WEIGHTED.md](NEXT_SFT_S8_WEIGHTED.md) (RAG + open-theology,
seq 4608, `SFT_EXPORT=0`), but on **RunPod** with **`SFT_BACKEND=unsloth`**.

Vast PEFT remains the fallback. Do **not** call
`vast_sft_s8_weighted_orchestrate.ps1` or GATE-0 `sft_orchestrate.ps1` for this path.
No rent until the operator says **go**.

## Why RunPod Unsloth

Vast PEFT at seq 4608 measures ~90 s/step × 514 ≈ 13 h. Vast Unsloth SIGSEGVs for this
job. RunPod + isolated setup (`sft_remote_setup.sh` with backend=unsloth) is the speed bet.
Full go only after a smoke proves s/step clearly beats ~90s.

## Dry (no rent)

```powershell
cd fine_tuning\scripts
.\runpod_sft_s8_weighted_orchestrate.ps1
```

Expect `READY` and `DRY COMPLETE`, plus `PINNED_SHA=...`, `HOST=runpod BACKEND=unsloth`,
and `DIRTY_OVERRIDES=(none)` (or a list). That command does not call runpodctl, scp, or ssh.

## Smoke go (after operator go)

```powershell
cd fine_tuning\scripts
.\runpod_sft_s8_weighted_orchestrate.ps1 -Go -SmokeOnly -StartMonitor
```

Provisions Community RTX 4090 on US-IL-1 with network volume `7hb931c5oe`, sparse-syncs at
`PINNED_SHA`, runs setup + 2-step smoke at 4608 with `SFT_BACKEND=unsloth`, then exits on
`SMOKE_ONLY_DONE`. Fetch evidence, destroy pod. Budget target under ~$1.

## Full go (only if smoke s/step wins)

```powershell
cd fine_tuning\scripts
.\runpod_sft_s8_weighted_orchestrate.ps1 -Go -StartMonitor
```

Push the pin before `-Go`. Dirty sync paths need `-AllowDirtySync`.

## Train contract

| Knob | Value |
|------|--------|
| Host | RunPod (Community 4090 → Secure fallback) |
| Image | `runpod/pytorch` from `sft_runpod_common.ps1` |
| Base | private Hub `rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit` |
| Pod path | `/workspace/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit` |
| Backend | `SFT_BACKEND=unsloth` (bf16 LoRA; not QLoRA) |
| Seq / batch / accum | 4608 / 1 / 16 |
| Open theology | `SFT_OPEN_THEOLOGY=1`, repeat 1 |
| Output | `/workspace/sft_s8_weighted/adapter` |
| Export | `SFT_EXPORT=0` until F §5 |
| Session | `fine_tuning/kaggle/runpod_sft_s8_weighted_session.json` |
| Fetch dir | `fine_tuning/kaggle/runpod_sft_s8_weighted/` |
| Label | `sft-s8-weighted-unsloth` |

Launcher: `sft_remote_train_s8_weighted.sh` (honors `SFT_BACKEND` / `SFT_SMOKE_ONLY`).

## Walk-away gates

Forge must see:

- `SFT_OPEN_THEOLOGY=1`
- `RAG_PROMPT_OK` and `THEOLOGY_PROMPT_OK`
- `RAG_ROWS` / `OPEN_THEOLOGY_ROWS` / `MIX_ROWS` (~3264 / ~558 / ~3822)
- Base under `.../qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit`
- `SFT_BACKEND=unsloth` (or `SFT_BACKEND: unsloth`)
- `SFT_EXPORT=0`
- `SFT_OUTPUT_DIR` under `sft_s8_weighted`
- **not** `Resuming from .../spurgeon_qa_lora_v2`
- Smoke: `SFT_SMOKE_PASS` then `SMOKE_ONLY_DONE` (smoke-only) or `FULL_TRAIN` (full)

## Ops rules

- Fetch before destroy. Volume keeps merge between pods; do not wipe CPT trees on the volume.
- Hub LoRA v2 `06354dfc` and `spurgeon-qa-v2` stay.
- Do not drop seq below ~4330 without operator go.
- If Unsloth SIGSEGV / setup fail: evidence + destroy; fall back to Vast PEFT orchestrator.
