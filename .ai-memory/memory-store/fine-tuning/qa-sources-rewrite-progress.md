---
store_path: fine-tuning/qa-sources-rewrite-progress
title: "QA Sources Rewrite Progress"
summary: "Cross-session log of QA answer rewrite pipeline for SFT teacherish/quote fidelity"
priority: high
tags: [fine-tuning, qa-rewrite, stop-point]
schema_version: 1.3
last_updated: "2026-09-02T08:58:42-04:00"
---

# QA Sources Rewrite Progress

Cross-session log of QA answer rewrite pipeline for SFT teacherish/quote fidelity.

## Pipeline overview

1. `rewrite_qa_answers_teacher.py --apply` → writes candidates to `bulk_pending.jsonl`
2. `review_qa_rewrite_bulk.py` → human/auto review
3. `merge_qa_bulk_rewrite.py` → merges approved into QA mix overlay
4. `12_package_kaggle_qa_mix.py` → repackage for Kaggle
5. `audit_qa_mix_quality.py` → gate checks (quote %, teacherish count, caricature)
6. `13_sft_local_readiness.py` → final SFT readiness check

## Milestone history

### 2026-08-29 session — Quote gate MET, teacherish ~76 short

**Metrics snapshot:**
- Quote coverage: **15.8%** (419/2655 answerable with CONTEXT quote) — **15% gate MET**
- Teacherish: **324** total (gold 20 + bulk 304 unique) — target ≥400, ~76 short
- Caricature: **0**
- Bulk merged: **304 unique** in overlay
- `13_sft_local_readiness`: **PASS**
- Train: **3013 rows** (90 catechism)

**Resume point:** next unprocessed row = line **649** in `qa_mix_train.jsonl` (last processed: 648).

**Provider learnings this session:**
- Groq 120b best quality but TPD ~197k/200k exhausted; resets ~3 AM ET
- Groq 20b available, ~30% pass rate
- Cerebras daily quota exhausted
- Gemini/OpenRouter: API OK, poor quote fidelity (backup only)
- Ollama not running locally

**Operational rules established:**
- Single provider on `--apply` only (no parallel writes to `bulk_pending.jsonl`)
- Do not run `build_qa_mix_v2.py` or GPU D→E→F without explicit operator go
- Dedupe backup: `bulk_pending.jsonl.bak.20260830T004257Z`
- Fixed null Cerebras content via `_extract_chat_content()` (dataset row 307)
- TEACHER_SYSTEM rule 5 strengthened for verbatim quotes

**Gate status:**
| Gate | Status |
|------|--------|
| Quote ≥10% | MET (15.8%) |
| Teacherish ≥400 | NOT MET (~76 remaining) |
| Caricature = 0 | MET |

**Next action:** continue rewrite from line 649; ~2–3 batches of 50 to clear teacherish gate.

## 2026-08-30 morning — Teacherish gate MET (401)

**Metrics:** quote 18.0% (478/2655); teacherish **401** (gold 20 + bulk 381); caricature 0; `13_sft_local_readiness` PASS; train 3013.

**This session batches:**
- Groq 120b from line 649: 9 OK then TPD ~198k/200k (killed retries)
- Groq 20b: 12 OK then TPD exhausted
- Cerebras: 31/50 then 24/50 (best remaining provider)
- Merged unique bulk 304 → 381

**Resume if continuing:** next unprocessed line **803**. Gates already met; further rewrite is optional lift. Do not run `build_qa_mix_v2.py` or GPU without operator go.

## 2026-08-30 afternoon — continue with available providers

Lifted teacherish **401 → 489**, quote **18.0% → 20.2%** (536/2655). Bulk unique 381 → 469.

Batches: Cerebras 30/50 + 26/50 then token_quota; Groq 120b brief recover then TPD; Groq 20b TPD; OpenRouter 6/50; Gemini smoke 3/5.

Resume line **1008**. Prefer Gemini for more today; Cerebras/Groq after daily reset.

## 2026-08-30 mid-afternoon — Gemini + OpenRouter continue

Gemini from 1008: 6 OK then quota. OpenRouter two batches: 12/50 + 17/50. Teacherish **489→524**, quote **20.2%→20.7%** (550/2651), bulk unique 469→504. Resume **1125**. Only OpenRouter still usable today among cloud teachers.

## 2026-09-02 — Pass 1 complete; retry-drops paused

**Stop state:**
- Pass 1: **3244/3244** non-gold lines attempted (`bulk_pending` has every line).
- Pass 2 `--retry-drops`: **1778** lines still without `ok=true`; **1466** unique ok.
- Merged into train: **1465** bulk + 20 gold → **1485** teacherish; quote **49.1%**.
- ~**1438** rows still "originalish" in train (mixed legacy + teacher answers).

**Tooling added:** `rewrite_qa_rotate_providers.py` (--retry-drops, --providers filter); `rewrite_qa_answers_teacher.py --retry-drops`; merge retry on Windows PermissionError.

**Resume:** `rewrite_qa_rotate_providers.py --retry-drops`; prefer cerebras after daily reset else `--providers groq,openrouter,gemini`.

**SFT:** dry-run ready (readiness PASS); zip needs repack; operator go for GPU; CPT S6 still incomplete for final merge.

## 2026-09-02 morning — Pass 2 retry-drops continue

**Stop state (live ~09:00 ET):**
- Pass 1 complete: 3244/3244 attempted.
- Pass 2: **1734** drop rows remain; **1510** unique ok in `bulk_pending.jsonl`.
- Merged: **1539** bulk + 20 gold → **1559** teacherish.
- Quote **51.5%** (1471/2855); caricature 0; originalish ~1364.
- `13_sft_local_readiness` PASS.

**Session delta from handoff start:** teacherish +67 (1492→1559), quote +2.2pp, bulk merged +67.

**Batches:** OpenRouter 3/15 ok; background `rewrite_qa_rotate_providers.py --retry-drops --providers openrouter,gemini,cerebras,groq --max-rounds 3` still running (Cerebras Round 1). Log: `rotate_session_log.txt`.

**Providers:** OpenRouter best pass rate; Cerebras steady; Groq 429-heavy.

**Resume:** same rotate command; prefer OpenRouter when limits allow.

**SFT:** dry-run ready; repack zip before upload; optional rewrite lift only.
