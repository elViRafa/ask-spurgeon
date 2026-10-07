---
store_path: pretraining/cpt-s8-mhi-resume-c-merge-parent
title: "S8 Isolation C rebuilds merged a70 before eval"
summary: "Isolation C instance 54545345 failed from_pretrained (rc=4) because resume adapter 22698039 has adapter_config.base_model_name_or_path=/workspace/theology_cpt_merged_a70 and the C pod did not have tha"
priority: high
tags: [cpt, s8, isolation-c, merge-parent, grok, forge]
schema_version: 1.3
last_updated: "2026-10-07T07:58:21-03:00"
evidence: [continued_pretrain/scripts/vast_cpt_s8_mhi_resume_c_eval.ps1, continued_pretrain/scripts/vast_remote_stack_isolation_c.sh, "commit:638a249"]
---

Isolation C instance 54545345 failed from_pretrained (rc=4) because resume adapter 22698039 has adapter_config.base_model_name_or_path=/workspace/theology_cpt_merged_a70 and the C pod did not have that directory.

Fix is open PR 10 (branch fix/s8-mhi-resume-c-merge-parent, commit 638a249). -Go syncs merge parent a70fded8 from vast_cpt_s7_p0/fetch/theology_cpt_lora_s5best plus fine_tuning/scripts/merge_cpt_lora.py, then vast_remote_stack_isolation_c.sh rebuilds /workspace/theology_cpt_merged_a70 before eval. Do not remap the adapter onto stock Qwen. EVAL_BASE stays unsloth/Qwen3.5-4B-Base. Hub stays Phase A 06354dfc until section 5 wins.

Operator-PC dry printed READY on 2026-10-07. Pytest 8 passed. Rafael will run -Go in Grok Bot from that branch. Cursor does not rent. Vast snapshot at 07:56 America/Sao_Paulo: credit $6.34, 0 instances. Re-check before rent. Do not launch from main.
