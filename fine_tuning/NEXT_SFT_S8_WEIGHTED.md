# Next job — Weighted SFT on S8 merged CPT (RAG + open-theology)

Train one PEFT LoRA on the S8 m_hi resume merged 16-bit weights with **two
datasets kept as separate files**. Hub LoRA v2 stays Phase A `06354dfc`.
`spurgeon-qa-v2` stays. `SFT_EXPORT=0` until F §5.

**Secondary host (Unsloth speed bet):** RunPod — see
[NEXT_SFT_S8_WEIGHTED_RUNPOD_UNSLOTH.md](NEXT_SFT_S8_WEIGHTED_RUNPOD_UNSLOTH.md)
(`runpod_sft_s8_weighted_orchestrate.ps1`, `SFT_BACKEND=unsloth`). Do not replace
this Vast PEFT path until Unsloth smoke proves faster and stable.

## Why weighted

The frozen RAG mix teaches CONTEXT-only Q&A. The open-theology slice teaches
open answers with `THEOLOGY_CHAT_SYSTEM_PROMPT`. Concatenating the JSONL files
would rewrite theology rows onto the RAG system prompt inside
`train_sft_sota.py`. This job keeps both prompts and samples each train row
once (repeat **1**, no upsample).

| Slice | File | Rows (2026-10-13) | System prompt |
|-------|------|-------------------|---------------|
| RAG | `fine_tuning/data/qa_mix_train.jsonl` | 3264 | `SPURGEON_SFT_SYSTEM_PROMPT` |
| Open theology | `fine_tuning/data/qa_open_theology/sft/open_theology_train.jsonl` | 558 | `THEOLOGY_CHAT_SYSTEM_PROMPT` |
| Mix | in-memory shuffle | 3822 | both |

Trainer val stays `qa_mix_val.jsonl` only. `open_theology_eval.jsonl` (40 rows)
is copied for a later eval and is **never** trained. Do not run
`build_qa_mix_v2.py`. Do not merge open-theology into the RAG mix.

## Dry (no rent)

```powershell
cd fine_tuning\scripts
.\vast_sft_s8_weighted_orchestrate.ps1
```

Expect `READY` and `DRY COMPLETE`, plus a sync banner: `PINNED_SHA=...`,
`SPARSE_CONE=fine_tuning/data fine_tuning/scripts`, and `DIRTY_OVERRIDES=(none)`
(or a list of dirty sync paths). That command does not call vastai, scp, or
ssh. `-Go` is for Forge after the operator says go and Vast credit covers the
quote (top up if credit is under ~`$5`).

## Sync on -Go (no bulk jsonl SCP)

The GPU pulls tracked data/scripts from public GitHub at the laptop’s
`PINNED_SHA` (shallow cone sparse-checkout of `fine_tuning/data` +
`fine_tuning/scripts`, then materialize into `/workspace/...`). SCP is only
for dirty sync-path overrides, and only with `-AllowDirtySync`. Push the pin
before `-Go` so `git fetch origin <SHA>` succeeds on the pod. Do **not** SCP
`qa_mix_train.jsonl` when the tree is clean.

## Train contract (when Forge is told go)

| Knob | Value |
|------|--------|
| Base | private Hub `rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit` |
| Pod path | `/workspace/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit` |
| Backend | `SFT_BACKEND=peft` (Unsloth SIGSEGVs on Vast) |
| Seq / batch / accum | 4608 / 1 / 16 |
| Open theology | `SFT_OPEN_THEOLOGY=1`, `SFT_OPEN_THEOLOGY_REPEAT=1` |
| Output | `/workspace/sft_s8_weighted/adapter` |
| Export | `SFT_EXPORT=0` until F §5 |
| Session | `fine_tuning/kaggle/vast_sft_s8_weighted_session.json` |
| Fetch dir | `fine_tuning/kaggle/vast_sft_s8_weighted/` |
| Label | `sft-s8-weighted` |

Launcher on the pod: `fine_tuning/scripts/sft_remote_train_s8_weighted.sh`.
It downloads the private merge if absent, then runs `train_sft_sota.py`. It
does not call `sft_remote_merge.sh` and does not upload.

```powershell
cd fine_tuning\scripts
.\vast_sft_s8_weighted_orchestrate.ps1 -Go -StartMonitor
```

Do **not** call `vast_orchestrate.ps1`, `vast_sft_s8_orchestrate.ps1`, or any
CPT launcher for this job.

## Setup markers (`/workspace/sft_setup.log`)

Shared gating lives in `fine_tuning/scripts/sft_setup_markers.sh` (watchdog +
local monitor). Do **not** idle-destroy while the setup log is still advancing.

| Marker | Meaning |
|--------|---------|
| `SETUP_PHASE=boot` | Script start (CUDA diagnostics, pre-torch probe) |
| `SETUP_PHASE=pins` | Pin install in progress (long pip is normal) |
| `SETUP_PINS_OK` / `SETUP_PHASE=pins_ok` | Pins asserted |
| `SETUP_OK` / `SETUP_PHASE=ok` | Isolated env ready |
| `SETUP_TRAP_INFO line=N cmd=… rc=…` | ERR trap noise. Never destroys. |
| `SETUP_FAILED rc=N` | Real abort (line must start with this). `die` or non-zero EXIT. |
| `SMOKE_BEFORE_TRAIN_FAILED` | Train-script smoke died (line must start with this) |
| `SETUP_HEARTBEAT …` | Pip/apt still moving (every 30s) |
| `FULL_TRAIN` | Full train started; watchdog exits healthy |

**Actionable fail:** a log line that **starts with** `SETUP_FAILED rc=` or
`SMOKE_BEFORE_TRAIN_FAILED`. Text that merely contains those words does not
destroy. `SETUP_TRAP_INFO` (including `|| true` and `set +e`) does not destroy.

**First launch after this fix:** orchestrator default `-WatchdogDry 1`. The
remote watchdog writes `WATCHDOG_DRY would destroy` and does not DELETE. The
pc1 monitor is the only destroyer. Pass `-WatchdogDry 0` after one clean setup.

**Before any remote destroy** (when dry is off): `WATCHDOG_DESTROY_BEGIN
reason=… trigger_line=<exact log line>` plus the last 200 log lines in
`/workspace/sft_fail_evidence/watchdog_destroy_begin.txt`, scp/rsync to
`SFT_EVIDENCE_PUSH_TARGET` when that env var is set on pc1.

**Watchdog silent timeout:** base grace ~25m, **extended while `sft_setup.log`
mtime/size advances**, cap ~90m; destroys only when the log is stale (~5m) and
there is still no `SETUP_OK`. Do not treat a quiet monitor as “stuck” during pin
install if the setup log is growing.

## Walk-away gates (`/workspace/sft_train.log`)

Forge must see all of these before walking away:

- `SFT_OPEN_THEOLOGY=1`
- `RAG_PROMPT_OK` and `THEOLOGY_PROMPT_OK`
- `RAG_ROWS` / `OPEN_THEOLOGY_ROWS` / `MIX_ROWS` (expect ~3264 / ~558 / ~3822)
- `BASE_MODEL` or preflight base under `.../qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit`
- `SFT_BACKEND=peft` (log may show `SFT_BACKEND: peft`)
- `SFT_EXPORT=0` (from launch env / remote script)
- `SFT_OUTPUT_DIR: /workspace/sft_s8_weighted/adapter` (or under `sft_s8_weighted`)
- **not** `Resuming from .../spurgeon_qa_lora_v2`
- dataprep: `over 4608` near 0; `S3 masking OK`; drop fully-masked count near 0
- during setup: watch `/workspace/sft_setup.log` advancing — do not idle-destroy mid-`sft_remote_setup`
- OOM at 4608: keep seq; propose `SFT_LORA_RANK=16` and wait for go (do not drop seq below ~4330)

## After fetch

- Artifacts land in `fine_tuning/kaggle/vast_sft_s8_weighted/` (adapter + logs).
- Destroy the instance after a successful fetch (Vast has no network volume).
- Score the RAG path with `sft_export_if_gates.ps1` when ready. Export only if
  every F gate passes (refusal ≥ 0.85, groundedness ≥ 4.0, …).
- Open-theology scoring is a later eval on `open_theology_eval.jsonl`.
- Do not overwrite `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` or
  `spurgeon-qa-v2`.

## Forge paste (audit / dry first)

```text
Skill: /gpu-train-ops
Job: weighted SFT, not CPT.
Runbook: fine_tuning/NEXT_SFT_S8_WEIGHTED.md
Orchestrator: fine_tuning/scripts/vast_sft_s8_weighted_orchestrate.ps1
Seq 4608 / peft / SFT_EXPORT=0. Hub LoRA v2 06354dfc stays.
Dry only:
  cd fine_tuning\scripts
  .\vast_sft_s8_weighted_orchestrate.ps1
Expect PINNED_SHA + SPARSE_CONE + DIRTY_OVERRIDES=(none). Sync on -Go is
sparse-checkout on GPU; SCP only dirty overrides (-AllowDirtySync).
Do not rent. Report credit and the cheapest full RTX 4090 $/hr.
Wait for my go. -Go -StartMonitor only after I say go and credit covers the quote.
Credit under ~$5 needs a top-up or my explicit -AllowLowCredit.
Walk-away: SFT_OPEN_THEOLOGY=1, RAG/THEOLOGY_PROMPT_OK, peft, EXPORT=0,
base under qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit, output under
sft_s8_weighted/adapter, over 4608 ~0, S3 masking OK, drop ~0.
Watch sft_setup.log advancing during setup — do not idle-destroy mid-setup.
Silent watchdog extends while the log grows (cap ~90m).
OOM: keep seq; propose SFT_LORA_RANK=16 and wait for go.
Do not call vast_orchestrate.ps1, vast_sft_s8_orchestrate.ps1, or any CPT launcher.
No Hub upload. Fetch before destroy.
```
