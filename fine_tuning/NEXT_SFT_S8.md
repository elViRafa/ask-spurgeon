# Next job — SFT on the S8 merged CPT (dry-ready, not rented)

Stop CPT resumes. Train a new supervised fine-tune on the S8 m_hi resume
merged 16-bit weights. Hub LoRA v2 stays Phase A `06354dfc`.

## Why this job

Isolation C on adapter `2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207`
(step 2250, 2026-10-07) is the best theology score and still missed section 5.

| Bucket | Untrained base | Hub Phase A | S8 C |
|--------|----------------|-------------|------|
| spurgeon | 14.31 | 12.45 (−13.0%) | 11.88 (−17.0%) |
| puritan | 6.03 | 5.52 (−8.6%) | 5.26 (−12.8%) |
| confession | 5.61 | 5.27 (−6.0%) | 5.01 (−10.7%) |
| general | 12.05 | 11.95 (−0.8%) | 12.50 (+3.8%) |

Puritan loss **1.6605** vs gate **1.6349** (gap **0.0256** nats). The HF-resume
from step 800 to 2250 moved in-train puritan only **1.708 → 1.701**. Another
resume at 5e-6 does not buy the remaining gate, and general is already worse
than the untrained base.

The product model is the Q&A speaker. GATE-0 `spurgeon-qa-v2` (older CPT merge)
scored groundedness **4.51**, stop **100%**, corrupt **0%**, and refusal recall
**0.54** vs **0.85**. That release miss is an SFT gate. This job changes one
knob: the CPT base. The QA mix and the PEFT 4090 recipe stay the ones that
already cleared groundedness.

## Dry (no rent)

```powershell
cd fine_tuning\scripts
.\vast_sft_s8_orchestrate.ps1
```

Expect `READY` and `DRY COMPLETE`. That command does not call vastai, scp, or ssh.
`-Go` is refused. Forge rents only after a later operator go.

## Train contract (when Forge is told go)

| Knob | Value |
|------|--------|
| Base | private Hub `rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit` |
| Pod path | `/workspace/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit` |
| Backend | `peft` (Unsloth SIGSEGVs on Vast) |
| Seq / batch / accum | 2048 / 1 / 16 |
| Export | `SFT_EXPORT=0` until F §5 |
| Mix | existing `qa_mix_train.jsonl` (do not rebuild) |
| Stack | torch 2.11 + PEFT, via `sft_remote_setup.sh` |

Launcher on the pod: `fine_tuning/scripts/sft_remote_train_s8.sh`. It downloads
the private merge if the folder is absent, then runs `train_sft_sota.py`. It
does not call `sft_remote_merge.sh` and does not upload.

## After fetch

Score with `sft_export_if_gates.ps1`. Export only if every F gate passes,
including refusal ≥ 0.85 and groundedness ≥ 4.0. If refusal is still the only
miss, the next knob is the refusal slice. If groundedness falls under 4.0,
keep this adapter experimental and the fallback base is the older GATE-0 merge,
not another CPT resume.

Do not overwrite `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` or
`spurgeon-qa-v2`.
