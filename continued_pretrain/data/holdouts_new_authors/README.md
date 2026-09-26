# New-authors diagnostic holdout (Downame + wave 5)

Monitor-only probe for the v6 holdout-sibling replay CPT. **Not** part of §5,
`COMPOSITE_EARLY_STOP_METRICS`, or Hub promote. Do **not** copy into
`holdouts/` or `holdouts_pinned_v3/`.

## Build (operator machine with corpus)

Requires `continued_pretrain/data/puritans/{downame,ambrose,swinnock,venning,binning,preston,durham,vincent,guthrie}/…`
(see `NEXT_CPT_S7.md` shelf table).

```text
python continued_pretrain/scripts/19_build_new_authors_holdout.py
```

Writes `new_authors_holdout.txt` + `MANIFEST.json` (SHA256 of the concat) here.
Optional HF pack into existing `a_output_v6` without rewriting the train set:

```text
python continued_pretrain/scripts/19_build_new_authors_holdout.py ^
  --hf-out-dir continued_pretrain/kaggle/a_output_v6/theology_holdouts
```

Then rebuild mix_v6 with `--new-authors-holdout` and prep HF with
`--extra-holdout-dir continued_pretrain/data/holdouts_new_authors`
(see `NEXT_CPT_S7.md`).
