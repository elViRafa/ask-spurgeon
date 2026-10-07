---
store_path: pretraining/cpt-v4-continue-reweight
title: "CPT v4 continue: reweight new authors, keep old corpus"
summary: "Use this when preparing the GPU CPT for the Downame + wave 5 corpus (`a_output_v4` shelf)"
priority: high
tags: [cpt, phase-b, a-output-v4, reweight, continue, downame, wave5]
schema_version: 1.3
last_updated: "2026-09-23T10:37:02-03:00"
evidence: [[REDACTED_SECRET].json, continued_pretrain/data/theology_mix_manifest.json, continued_pretrain/NEXT_CPT_S7.md, data/puritans/PROVENANCE.md]
---

# CPT on this corpus: continue, reweight, do not train new authors alone

Use this when preparing the GPU CPT for the Downame + wave 5 corpus (`a_output_v4` shelf). Decided 2026-09-23.

## Start point

- Init adapter: Hub private `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` = S7 s5best SHA `06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432`
- That adapter trained on frozen `continued_pretrain/kaggle/a_output_v3` SHA `23dd3820baa0b657cb6528e4fdf1b2d4813c3cfa7b7c982805b4a7ff34990973`
- It has never seen John Downame or wave 5 (Ambrose, Swinnock, Venning, Binning, Preston, Durham, Vincent, Guthrie)
- Load that LoRA on Qwen3.5-4B-Base with a **new Adam**. Do not HF-resume the v3 optimizer or dataloader. Do not point the run back at `a_output_v3`. Packing stays `one_doc_padded`.

## Corpus fact

Packed `continued_pretrain/kaggle/a_output_v4` SHA `37a3ba50aa9efb8057d9d36227ac4547f08d35a31ccd71cf3f2d20f928131c81` is the **superset**: old shelf plus 11 new files (~14.2M chars: ~5.7M Downame + ~8.5M wave 5).

- New files are ~4% of ~332M train characters and ~9% of the Puritan bucket (Puritan 47.8% / Spurgeon 38.4% / general 7.2% / confession 5.3% / Bible 1.3%).
- A uniform epoch on this pack mostly re-reads text the S7 adapter has already fitted (~one epoch on v3).
- Repeating the 11 files ~2x only lifts them to ~8%. ~4 copies to reach ~15% is enough to memorize those books.

## What to train

Keep the full mix. Do **not** run a new-authors-only CPT.

- Puritan holdouts are pinned v3 probes drawn from the **older** Puritan shelf. Sibling chunks of those works stay in train. Gradients on the old shelf move that gate directly. The new books help that gate only by transfer.
- Confession (~17M chars, the other half of the §5 −15% gate) is absent from the new files. A new-authors-only run has no confession tokens.
- Spurgeon is already 12.45 (−13% vs base 14.31). A Puritan-only continue drops rehearsal of that number.

Reweight before the GPU copy:

- Keep Spurgeon, older Puritans, confession, Bible, and general replay as the **majority**.
- Raise the 11 unseen files to a real minority, about **15%** of steps.
- Prefer **one pass** over those 11 files plus a subsample of the already-trained shelf, so the old buckets stay the majority without four copies of the new books.
- Same pinned holdouts (`continued_pretrain/data/holdouts_pinned_v3`). Do not redraw them. C will not report a separate loss for Downame or wave 5.
- Reweight changes the mix, so pack a **new SHA**. Leave `a_output_v3` untouched. Do not overwrite v4 in place if that SHA has already been copied; write the reweighted pack to a new `a_output` directory.

## Clean audit before the reweight

Any orthography, boilerplate, or OCR-identity fix is corpus-wide (all Puritans, hymns, confessions, Bible, Spurgeon, replay), not new-authors-only. `data/**/*.txt` had no remaining long-s (`ſ`) on 2026-09-23. Rebuild the full mix only if a source file actually changes. Spurgeon's `clean_md_sermon` does not apply the long-s map; `clean_generic_text` does.

## Still out

- Confession S5 (Shaw, Sum of Saving Knowledge) unless 6% of the rebuilt mix exceeds confession already on disk (~30.7 MB)
- Gillespie polity, Durham commentaries, Vincent WSC, Fisher, Savoy, Henry exposition, Turretin English, Banner/Heritage/Puritan Publications bodies
- Hub overwrite until a winning C on the pinned probes

## Gate this continue is for

§5 −15% on puritan and confession vs this C's Ampere base, Spurgeon not worse than ~12.85 by more than ~1 PPL, general ≤ +10% vs base. C on Unsloth 2026.8.22 + torch 2.8.
