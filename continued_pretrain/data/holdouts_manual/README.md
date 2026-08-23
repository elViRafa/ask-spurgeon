# Manual doctrine holdouts (do **not** train on these)

Files here are for **evaluation only** (Heidelberg MCQ / generalization probes).

- `heidelberg_catechism.txt` — held out from `data/confessions/`
- Add `belgic_confession.txt` when available (also hold out)

**Never** pass this directory to `07_build_theology_mix.py` as a training source.
