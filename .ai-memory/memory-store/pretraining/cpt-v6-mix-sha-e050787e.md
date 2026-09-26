---
store_path: pretraining/cpt-v6-mix-sha-e050787e
title: "v6 mix SHA pin e050787e after new_authors"
summary: "After rebuilding mix_v6 on pc1 to exclude `new_authors` diagnostic holdout fingerprints, `mix_sha256` moved:"
priority: high
tags: [cpt, s7, v6, mix-sha, foundry]
schema_version: 1.3
last_updated: "2026-09-26T16:08:03-03:00"
---

## Mix SHA pin bump (2026-09-26)

After rebuilding mix_v6 on pc1 to exclude `new_authors` diagnostic holdout fingerprints, `mix_sha256` moved:

- **was:** `2d5a99c1a0d4d3e4d64013dabe894a52f4de1bf0b576e8997b02af595f691acd`
- **now:** `e050787e138e3d082937e35d1a87aa139f8e980403c3e5fefcc55aa90a2465fc`

Applied on pc1 working tree / branch: `$MixSha` in `vast_cpt_s7_common.ps1`, `EXPECT_MIX` in `vast_cpt_s7_local_readiness.py`, `NEXT_CPT_S7.md`.

Box commit ready on `chore/cpt-v6-mix-sha-e050787e` (`e3ac437`); GitHub push blocked from group-chat Auto-review — push/PR from DM or pc1 when possible.

Forge may re-dry once pc1 pin is live. No rent until go.
