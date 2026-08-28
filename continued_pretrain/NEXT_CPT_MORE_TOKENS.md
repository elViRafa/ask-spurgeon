# Next CPT — use more of the mix (after C)

**Do not run this instead of S5 C.** Next GPU session is C. This file is the playbook **if** C says more tokens are worth it.

S5 B early-stop at **375 / 4128** (~8.2M of ~90M tokens). The 2-doc Spurgeon probe flattened; `eval_mix` was still falling. Lower LR can make it *safe* to walk the rest of the mix. It does not replace unread tokens.

Related: `pretraining/cpt-future-b-early-stop-scale`, `pretraining/cpt-next-b-more-tokens-playbook`.

---

## Decide from C first

Compare S5 C to (1) **this C’s Ampere bf16 base** and (2) **v2 Ampere C** (spurgeon 13.28 / puritan 5.68 / confession 6.73 / general 13.20).

| C outcome | More-data B? |
|-----------|----------------|
| Worse than **own base** (probe FAIL) | **No.** Do not pour 80M tokens into a harmful adapter. Keep Hub v2. Diagnose. |
| Worse than **v2 Ampere C** on most buckets | **Low priority.** Keep Hub v2. Optional continue only if confession/puritan are the miss and spurgeon is OK. |
| ~v2 or better, but confession/puritan still far from §5 −15% | **Yes — preferred case.** Those buckets are 5.5% / 45.7% of the mix; 8.2M tokens only gave them a thin slice. |
| Already near §5 | **Probably skip** a 6–9 h epoch. Ship decision, not more GPU. |

Gains will not scale 11× with tokens. Expect a few more PPL points, not 11× the v2 −5% to −7%.

---

## Preferred continue (not a from-scratch 1e-5 rerun)

**Load S5 LoRA weights, new optimizer, lower LR, early-stop floor.**

Why not `trainer.train(resume_from_checkpoint=…)`:

- Pod `pul3xia882ub5r` was deleted. Volume was never mounted.
- Local copy is **adapter only** (`kaggle/runpod_cpt_v3/theology_cpt_lora`). No `optimizer.pt` / `trainer_state.json`.
- `PREV_RUN_CHECKPOINT` resume **cannot** be used for this continue until someone implements PEFT-load-adapter (code change, approval).

Practical start: `unsloth/Qwen3.5-4B-Base` + this LoRA (SHA256 `ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303`), Ampere bf16, same pack recipe.

### Recipe deltas (implement only when that B is approved)

Keep: `one_doc_padded`, r=32, GDN LoRA, embed FT, abort-at-50 **off or loosened** on a continue (loss is already low; 25→50 noise must not kill the run).

Change:

1. **Body LR ~3e-6 to 5e-6** (from 1e-5). Emb LR ~1e-6 to 2e-6 (from 5e-6). Short warmup (not 3% of 4128 if that is ~124 full-LR-adjacent steps).
2. **Cosine over the continue’s `max_steps`** (`LR_SCHEDULER=cosine` already). S5’s cosine was aimed at 4128 and **never ran its tail** because stop was at 9%.
3. **Early-stop floor** so patience cannot fire before the mix is actually used, pick one:
   - `min_steps` ≈ 0.4–0.5 packed epoch (~1650–2060), or
   - `min_tokens` ≈ 25–40M, or
   - patience scaled with `packed_epoch_steps / eval_steps` (patience 2 was for ~674-step runs; ~16 would be 0.1 epoch at eval 25).
4. Keep `QuietEarlyStoppingCallback`. Optional: more than 2 Spurgeon eval docs on 24 GB, or require mix not rising.
5. **Same mix.** Do not rebuild. `kaggle/a_output_v3`, mix SHA256 `23dd3820baa0b657cb6528e4fdf1b2d4813c3cfa7b7c982805b4a7ff34990973`.

### “Unread data” vs reshuffle

A new `train()` with `seed=42` **reshuffles**. You will **re-see** much of the first 8M plus new rows — not a clean suffix of step 376–4128. That is acceptable at lower LR (gentle replay). A true unread suffix needs a skip/`ignore_data_skip` (not in the trainer today). Do not claim “only new tokens” unless that skip is built.

### Cost / infra

- Full packed epoch still ~4128 steps × ~8–11 s ≈ **6–12 h** on 4090. `--terminate-after` ≥ 14 h.
- **Scp optimizer + `checkpoint-*` (or attach volume `7hb931c5oe`)** so the next interrupt can true-resume. S5 lost Adam state by deleting a mountless disk.
- MCP `create-pod` still drops the volume. runpodctl + API key, or accept disk + scp **including ckpts**.
- Do not overwrite Hub `…-cpt-lora-v2` until the new adapter beats v2 Ampere C.

### Do not

- Fresh 1e-5 from base just to “use the mix” — throws away the 8M already in this LoRA unless C showed the adapter is harmful.
- Treat 2-doc `eval_spurgeon` CE as “learning done.”
- Continue on T4 4-bit. Do not resume Kaggle 4-bit ckpts.
- Change packing back to concat.

---

## After that B

C the **new** adapter vs **its** Ampere base. Keep Hub v2 if worse. Merge still §5 −15% on puritan+confession.
