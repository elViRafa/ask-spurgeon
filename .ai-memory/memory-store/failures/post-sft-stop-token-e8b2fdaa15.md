---
store_path: failures/post-sft-stop-token-e8b2fdaa15
title: "Post-SFT stop-token phases falsely failed raw-ID generations, while Ollama API s"
summary: "Post-SFT stop-token phases falsely failed raw-ID generations, while Ollama API stops could falsely pass after stripping leaked im_start turns"
priority: medium
tags: [evaluation, failure, fix, ollama, sft, stop-tokens]
schema_version: 1.3
last_updated: "2026-09-07T22:16:20-04:00"
occurrences: 1
error_signature: "post-sft stop-token phases falsely failed raw-id generations, while ollama api stops could falsely pass after stripping leaked im_start turns."
---

## Occurrence 1 — 2026-09-07T22:16:20-04:00

**Error:**
Post-SFT stop-token phases falsely failed raw-ID generations, while Ollama API stops could falsely pass after stripping leaked im_start turns.

**Fix:**
Treat raw im_end token IDs as authoritative; for Ollama compliance use raw ChatML and configure only im_end as the stop so im_start leaks remain visible; phase 3 recomputes from raw stop probes and phase 5 fails whenever the complete summary fails.
