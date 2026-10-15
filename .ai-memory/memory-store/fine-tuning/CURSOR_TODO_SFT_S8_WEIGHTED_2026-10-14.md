# Cursor TODO - weighted SFT S8 (2026-10-14)

Do not change recipe knobs. Do not stage fine_tuning/data/qa_open_theology/ (Clerk is still writing there). No GPU rent, no Hub.

## 1. Commit + push pending fixes to main (currently uncommitted on pc1, main = c085120)
- SFT_MAX_SEQ_LENGTH=4608 in sft_remote_train_s8_weighted.sh and sft_s8_weighted_plan.py
- train_sft_sota.py: marker missing -> all labels -100; drop fully-masked rows (log count); S3 over all train+eval rows
- vast_common.ps1, vast_wait_ssh.ps1: ssh LogLevel=ERROR + Continue/$LASTEXITCODE
- test_mask_assistant_labels.py
Details: sft-label-mask-root-cause-2026-10-14.md

## 2. Fix scp in Copy-ToVastWeighted (vast_sft_s8_weighted_orchestrate.ps1 ~lines 98-112)
- scp opts: -C -o LogLevel=ERROR -o ServerAliveInterval=30 -o ServerAliveCountMax=10 -o ConnectTimeout=20
- ErrorActionPreference Continue around scp; check $LASTEXITCODE; retry 3x
- gzip large jsonl (qa_mix_train.jsonl ~37MB) before copy, gunzip on GPU
- log copy speed; abort if <200 KB/s or 37MB not done in 5 min
- optional: offer filter inet_down>=200
Details: sft-setup-stall-scp-2026-10-14.md

## 3. Optional
- Unsloth path in train_sft_sota.py (~line 1024) also call drop-fully-masked step.

## After
Foundry verifies commit read-only -> Forge dry run -> Rafael go (credit $4.69, needs -AllowLowCredit).
