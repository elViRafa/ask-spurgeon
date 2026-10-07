# S8 m_hi resume — merged 16-bit HF export (experimental)

Prepare and upload a **new** merged model repo. **Do not** overwrite production CPT LoRA v2 (`06354dfc`).

| Artifact | SHA / path |
|----------|----------------|
| Resume LoRA | `2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207` @ `vast_cpt_s8_mhi_resume/fetch/mhi_resume/theology_cpt_lora` |
| Merge parent | `a70fded8` @ `vast_cpt_s7_p0/fetch/theology_cpt_lora_s5best` |
| Local merged output | `fine_tuning/models/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit` |
| Default Hub repo | `rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit` (private) |

Isolation C §5 **miss** (puritan 1.6605 vs 1.6349); general holdout **+3.8%** vs base. Label the Hub README accordingly.

## 1. Local readiness (no GPU)

```powershell
cd C:\Users\rafael\Projetos\search-sermons
python fine_tuning\scripts\cpt_s8_mhi_resume_merge_readiness.py
pytest fine_tuning/scripts/test_merge_cpt_s8_mhi_resume_readiness.py -q
```

## 2. Who runs the GPU

Cursor writes this runbook and may run the dry orchestrator (no `vastai`). **Grok Bot owns the pod:** rent, merge, download the 16-bit folder to this PC, destroy. Cursor does not rent, SSH, scp, destroy, or upload.

Stages on the pod via `merge_cpt_s8_mhi_resume.py` (torch 2.8 + Unsloth 2026.8.22):

1. `a70` LoRA → `/workspace/theology_cpt_merged_a70`
2. Patched resume LoRA (base path → step 1) → `/workspace/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit`

The pod does not push to Hugging Face. Fetch lands at `fine_tuning/models/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit` (~8.5 GB; need ≥30 GB free). Destroy only after that copy has `config.json` and safetensor shards.

### Cursor dry (no GPU)

```powershell
cd C:\Users\rafael\Projetos\search-sermons\continued_pretrain\scripts
.\vast_cpt_s8_mhi_resume_hf_export_orchestrate.ps1
```

### Grok Bot (after operator go)

```powershell
cd C:\Users\rafael\Projetos\search-sermons\continued_pretrain\scripts
.\vast_cpt_s8_mhi_resume_hf_export_orchestrate.ps1 -Go
```

Walk-away gates: `PIN_OK`, stage-1 SHA `a70fded8`, stage-2 SHA `22698039`, `CPT_S8_MHI_RESUME_MERGE_DONE`, local folder present, instance destroyed. Do not call `vast_cpt_s8_mhi_resume_orchestrate.ps1 -Go` (that trains).

## 3. Cursor analyzes the local copy

Read-only. No upload, no SSH.

```powershell
python fine_tuning\scripts\cpt_s8_mhi_resume_merge_readiness.py --check-local
```

Pass prints `LOCAL_MERGED_OK`. A missing folder is expected until Grok Bot finishes `-Go`.

## 4. Grok Bot uploads from this PC

Only after `LOCAL_MERGED_OK`. `HF_TOKEN` in `.env` (write access). **Not** the production v2 LoRA repo. No `--public`.

```powershell
python fine_tuning\scripts\upload_cpt_s8_mhi_resume_merged_hf.py --dry-run
python fine_tuning\scripts\upload_cpt_s8_mhi_resume_merged_hf.py
```

Success URL: `https://huggingface.co/rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit`

Override repo: `--repo-id your-org/your-repo-name`.

## Do not

- Overwrite `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2`
- Merge resume LoRA directly on stock Qwen (base must be merged `a70` first)
- Upload from the pod, or upload before `LOCAL_MERGED_OK`
- Cursor renting, SSHing, fetching, destroying, or uploading
- Treat §5 miss as a production promote
- Start SFT on this merged base without an explicit operator decision (general regression)
