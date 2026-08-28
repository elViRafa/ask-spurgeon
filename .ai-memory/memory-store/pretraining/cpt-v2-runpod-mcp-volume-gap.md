---
store_path: pretraining/cpt-v2-runpod-mcp-volume-gap
title: "Runpod MCP create-pod objectMounts 400; REST v1 attaches volume"
summary: "As of 2026-08-28, hosted MCP `create-pod` GraphQL sends `objectMounts: null` / `tags: null`"
priority: high
tags: [cpt, runpod, mcp, volume]
schema_version: 1.3
last_updated: "2026-08-27T23:44:56-04:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/README.md, continued_pretrain/RUNPOD_RUNBOOK.md]
---

# Runpod CPT: MCP create-pod 400 objectMounts; REST v1 works

As of 2026-08-28, hosted MCP `create-pod` GraphQL sends `objectMounts: null` / `tags: null`. Runpod `PodFindAndDeployOnDemandInput` no longer has `objectMounts` → HTTP 400. This broke the path that worked for S5 B hours earlier.

`runpodctl` still has `no_credentials`. MCP OAuth bearer: REST **v2** and GraphQL **403**; REST **v1** `GET/POST https://rest.runpod.io/v1/pods` **200/201**.

S5 C workaround: POST REST v1 with `gpuTypeIds: ["NVIDIA GeForce RTX 4090"]`, `containerDiskInGb: 75`, `volumeInGb: 0`, `ports: ["22/tcp"]`, `env.PUBLIC_KEY`, `supportPublicIp: true`. Community had no instances. Secure US-IL-1 + `networkVolumeId: 7hb931c5oe` + `volumeMountPath: /workspace` **did attach** (B never got the mount). SSH key `~/.ssh/runpod_cpt`.

Do not search the filesystem for a Runpod API key. Prefer REST v1 until MCP drops `objectMounts` or a real `RUNPOD_API_KEY` exists for runpodctl.
