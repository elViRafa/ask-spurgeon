---
store_path: pretraining/cpt-s8-launch-blocked-credit
title: "S8 credit block cleared; Forge has the go"
summary: "On 2026-10-05 the operator asked to run the S8 CPT sweep on Vast"
priority: medium
tags: [cpt, s8, vast, credit]
schema_version: 1.3
last_updated: "2026-10-05T09:06:24-03:00"
---

On 2026-10-05 the operator asked to run the S8 CPT sweep on Vast. Local dry of vast_cpt_s8_sweep_orchestrate.ps1 printed READY. Live account credit was $2.98 and instance_count was 0. Cheapest matching RTX 4090 was offer 52377923 at $0.395/hr (Germany). The orchestrator refuses -Go when credit is under $5 unless -AllowLowCredit is passed. No instance was rented.

Estimated sweep is about 5h and about $2 at that rate. The script wall cap is 8h, which at $0.395/hr is about $3.16 and would exceed the current balance. Next step is add funds to at least $5, then run vast_cpt_s8_sweep_orchestrate.ps1 -Go. Do not start P1. Hub stays Phase A 06354dfc.

Superseded the same morning. At 09:03 America/Sao_Paulo credit was about $7.98 (above the $5 floor) and instance count was 0. Operator then assigned the launch to Forge. See `pretraining/cpt-next-session-handoff`.

Earlier block: dry READY, credit was $2.98, cheapest 4090 about $0.395/hr (offer 52377923, Germany). No instance was rented on that low balance.
