---
store_path: failures/full-semantic-judge-run-2188a7bf04
title: "Full semantic judge run stalled or failed due Groq/Cerebras 403, OpenRouter dail"
summary: "Full semantic judge run stalled or failed due Groq/Cerebras 403, OpenRouter daily quota 429, and transient Gemini 503 responses"
priority: medium
tags: [evaluation, failure, fix, llm-judge, rate-limit, resume, sft]
schema_version: 1.3
last_updated: "2026-09-07T22:16:20-04:00"
occurrences: 1
error_signature: "full semantic judge run stalled or failed due groq<path> <n>, openrouter daily quota <n>, and transient gemini <n> responses."
---

## Occurrence 1 — 2026-09-07T22:16:20-04:00

**Error:**
Full semantic judge run stalled or failed due Groq/Cerebras 403, OpenRouter daily quota 429, and transient Gemini 503 responses.

**Fix:**
Persist generation and judge progress, support judge-existing-report resume, batch order-swapped judgments, pin and verify one served judge model, and resume with Gemini 3.5 Flash Lite after transient failures without regenerating model outputs.
