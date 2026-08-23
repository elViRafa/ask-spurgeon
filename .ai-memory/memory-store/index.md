---
store_path: index
title: "Memory Store Index"
summary: "Index of all semantic memory store files."
priority: high
tags: [index, memory-store]
schema_version: 1.3
last_updated: "2026-08-23T11:10:53-04:00"
---

# Memory Store Index

Updated by Memory Fabric Dreaming mode `light`.

| Path | Priority | Summary | Key Topics | Tags |
| --- | --- | --- | --- | --- |
| `architecture/map-notes-pending-review` | medium | Hand-written notes folded from architecture.md; split into granular memories and delete. | • Folded from `architecture.md` on 2026-08-23T11:09:38-04:00<br>• Core Architecture Layers<br>• Key Subsystems | needs-review, legacy-map |
| `architecture/opcua-scada-simulation-platform` | high | OPC UA Industrial Engine & SCADA Simulation Platform | • OPC UA Server: `opc.tcp://0.0.0.0:4840/freeopcua/server/`...<br>• Device hierarchy: `Objects/IndustrialEngine/` with Folder...<br>• Telemetry & Physics: RPM, Coolant Temperature, Oil Pressu... | opcua, scada, python, asyncua, fastapi, simulation |
| `bugs/gemma4-chat-template-fix` | medium | Gemma 4 Chat Template Processor Fix | • Problem<br>• Solution | gemma4, chat-template, bugfix, unsloth |
| `bugs/lora-frozen-embeddings-special-tokens` | medium | Bug Fix: Training embed_tokens and lm_head when resizing vocabulary for special tokens in LoRA | • Context<br>• Problem<br>• Fix<br>• Update: PEFT Wrapper Attribute Lookup Error during Inference Copying (2026-06-15) | bugs, lora, embeddings, lm_head, special-tokens, unsloth |
| `bugs/ollama-tokenizer-corruption-fix` | high | Bug Fix: GGUF Vocab Shift and Alignment (具有战士/ _Parms) | • Context & Root Cause Discovery<br>• Solution | bugs, tokenizer, gguf, ollama, alignment |
| `bugs/sft-tokenizer-mismatch-vinfos-spepacer` | medium | ----- | • Context<br>• Root Cause Analysis<br>• Fixes Implemented | bugs, lora, tokenizer, qwen |
| `bugs/unsloth-embedding-offload-readonly` | high | Bug Fix: Unsloth Embedding Offload on Read-Only Filesystem | • Context<br>• Problem<br>• Fix | bugs, unsloth, embeddings, lora, kaggle, offloading |
| `bugs/unsloth-fast-patching-warnings` | medium | Unsloth Training Warnings & Fast Patching Resolution | • 1. LoRA Dropout Performance Warning<br>• 2. Gemma 4 Audio Tower Hook Registration Warning | unsloth, lora, gemma4, bugfix |
| `decisions/gemma4-finetuning` | medium | Guides the upgrade of fine-tuning pipelines from Gemma 2 to the efficient, newer Gemma 4 12B model. | • Rationale<br>• Configuration Details | gemma4, finetuning, decisions |
| `decisions/gemma4-local-ollama` | medium | Gemma 4 Local Ollama Deployment | • 1. Tokenizer List Parsing Bug Fix<br>• 2. Remote Streaming Conversion & Double Quantization<br>• 3. Importing into Ollama<br>• 4. Local Disk Cleanup (8B f16 Reclaim) | gemma4, ollama, gguf, quantization, cleanup |
| `decisions/map-notes-pending-review` | medium | Hand-written notes folded from decisions.md; split into granular memories and delete. | • Folded from `decisions.md` on 2026-07-09T20:55:33-04:00<br>• 1. Custom Model Fine-Tuning & Quantization (2026-06-01)<br>• 2. Memory Systems Integration (2026-06-01 to 2026-06-02)<br>• 3. Deployment & Performance Optimization (2026-06-02)<br>• 4. Local Execution Options (2026-06-02)<br>• 5. Grok + Memory Fabric Docs & Full Integration (2026-06-05)<br>• 6. Kaggle Model Saving Support (2026-06-05) | needs-review, legacy-map |
| `episodic/2026-07-11` | low | Episodic Journal — 2026-07-11 | • cpt-sota-pipeline | episodic, session-journal |
| `episodic/2026-07-12` | low | Episodic Journal — 2026-07-12 | • cpt-v2-plan | episodic, session-journal |
| `episodic/2026-07-13` | low | Episodic Journal — 2026-07-13 | • cpt-v2-model-selection<br>• cpt-plan-4b-flagship-tiering<br>• implement-cpt-v2-fable5<br>• fetch-puritan-corpus<br>• fetch-confessions-institutes<br>• cpt-v2-continue-kaggle-ready<br>• cpt-v2-preflight-max-steps | episodic, session-journal |
| `episodic/2026-07-14` | low | Episodic Journal — 2026-07-14 | • fn-sft-plan-fable5 | episodic, session-journal |
| `episodic/2026-08-12` | low | Episodic Journal — 2026-08-12 | • opcua-scada-simulation-platform<br>• copy-plan-to-agy-customizations | episodic, session-journal |
| `episodic/2026-08-23` | low | Upgraded and configured memory-fabric / ai-memory to v1.4.0 with field diary enabled (counts+queries) | • upgrade-memory-fabric-diary | episodic, session-journal |
| `failures/asyncua-write-value-badtypemismatch-188c68c9d2` | medium | asyncua write_value BadTypeMismatch when writing int to UInt16 or Double node wi | • Occurrence 1 — 2026-08-12T08:59:14-04:00 | failure, fix |
| `fine-tuning/data-generation-gemma4` | medium | Gemma 4 Local Dataset Generation Analysis | • Evaluation Results<br>• Implementation | fine-tuning, gemma4, dataset, ollama |
| `fine-tuning/gemma-support` | medium | Gemma 2 fine-tuning support scripts and configs. | • Updated train_spurgeon_qlora.py to read base model and ch...<br>• Configured launch_training.py to pass parameters dynamica...<br>• Added train_config_gemma.json configuration file. | gemma2, fine-tuning, ollama |
| `fine-tuning/qwen-sft-alpaca-reversion` | medium | Reverting Custom Model, Weight Copying, and ChatML in Qwen 2.5 SFT | • Context<br>• Reversion Decision<br>• Implementation Details | finetuning, qwen2.5, unsloth, alpaca, reversion |
| `grok/integration` | high | Grok Integration with Memory Fabric (MCP + Docs + Native Layer) | • Key Integration Points (as of 2026-06-04/05)<br>• Usage in Grok Sessions for this Project<br>• Windows / This Env Specifics<br>• Benefits for this Project | grok, mcp, memory-fabric, integration, docs, agents |
| `pretraining/bugs/sftconfig-pickle` | medium | Fixed SFTConfig Pickling Mismatch on Kaggle | None recorded | pretraining, unsloth, trl, sftconfig, pickle, bug-fix |
| `pretraining/confessions-corpus-fetch` | high | Confessions + Institutes corpus (WCF, 1689, Calvin) | • On disk under `data/confessions/` (~5.4 MB)<br>• Tooling<br>• Mix caps | pretraining, data, confessions, wcf, 1689, calvin |
| `pretraining/cpt-sota-assessment-2026-07` | high | CPT SOTA Assessment + Implementation (2026-07) | • Verdict on B_training.ipynb<br>• Baseline facts<br>• SOTA path implemented (new files only)<br>• Defaults<br>• Next operator steps | pretraining, cpt, unsloth, qlora, spurgeon, sota |
| `pretraining/cpt-v2-implementation-fable5` | high | CPT v2 implementation (Fable 5 plan) | • Code delivered<br>• Current mix (seed data)<br>• Operator next steps (Kaggle) | pretraining, cpt, v2, qwen3.5, mix, notebooks |
| `pretraining/cpt-v2-plan-fable5` | high | CPT v2 improvement plan (Fable 5 review, 2026-07-12) | • Critical findings (verify before next training run)<br>• v2 recipe deltas (from v1 sota)<br>• Success gate (ship v2)<br>• Base model decision (added 2026-07-12, plan §4.1)<br>• Base-model tiering revision (2026-07-13) | pretraining, cpt, base-model, qwen3.5, vram, flagship |
| `pretraining/cpt-v2-ready-for-kaggle` | high | CPT v2 ready for Kaggle (post local pipeline) | • Local pipeline complete<br>• M1 (partial pass)<br>• Remaining (operator / Kaggle only) | pretraining, cpt, kaggle, m1, mix, v2 |
| `pretraining/data-collection` | medium | Pretraining Step 1 — Data Collection Complete | None recorded | pretraining, dataset, sermons |
| `pretraining/dataset-preparation` | medium | Pretraining Step 6 — Dataset Preparation (Notebook A) Plan | • **Notebook A (`data_prep.ipynb`)** runs on CPU-only (acce...<br>• Ingests the cleaned training set `spurgeon_train.txt` and...<br>• Splits text documents on the `<\|endoftext\|>` marker, filt... | pretraining, dataset, kaggle, huggingface |
| `pretraining/environment-setup` | medium | Pretraining Step 5 — Environment Setup & Configurations | None recorded | pretraining, environment, kaggle, config, secrets |
| `pretraining/eval-and-export` | medium | Pretraining Step 8 (Schedule) and Step 9 (Evaluation & Export) | None recorded | pretraining, schedule, evaluation, export, notebook-c, perplexity |
| `pretraining/merge-and-export` | high | Pretraining Step 10 (Merge & Export to Hugging Face) | None recorded | pretraining, merge, export, gguf, huggingface, upload |
| `pretraining/model-choice` | medium | Pretraining Step 4 — Model Choice & Technical Rationale | None recorded | pretraining, model, qwen, vram |
| `pretraining/notebook-structure` | medium | Pretraining Step 3 — Kaggle Notebook Structure | None recorded | pretraining, kaggle, notebook, setup |
| `pretraining/puritan-corpus-fetch` | high | Puritan PD corpus fetch (Archive.org) | • Authors on disk<br>• Tooling<br>• Mix after rebuild | pretraining, data, puritans, archive-org |
| `pretraining/training-configuration` | medium | Pretraining Step 7 — Training Configuration (Notebook B) Plan | • **Notebook B (`training.ipynb`)** runs on 1x T4 GPU (16GB...<br>• VRAM is budgeted carefully (~7.55 GB usage, leaving ~8.45...<br>• Pinned installation of `unsloth[kaggle-new]` is used; man... | pretraining, training, lora, qlora, kaggle, unsloth |
