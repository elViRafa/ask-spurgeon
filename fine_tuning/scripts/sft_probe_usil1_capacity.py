#!/usr/bin/env python3
"""Probe US-IL-1 + volume 7hb931c5oe for creatable GPU types (no orchestration).

Deletes any pod that successfully creates (minimize billing).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from sft_provision_pod_mcp import (  # noqa: E402
    NETWORK_VOLUME,
    DATA_CENTER,
    http_json,
    load_mcp_token,
    pod_env,
)

PUBKEY = Path.home() / ".ssh" / "runpod_cpt.pub"

# ≥24GB, compatible with SFT; ordered cheap→expensive where sensible
CANDIDATES = [
    ("NVIDIA GeForce RTX 3090", "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404"),
    ("NVIDIA GeForce RTX 4090", "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404"),
    ("NVIDIA RTX A6000", "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404"),
    ("NVIDIA L40S", "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404"),
    ("NVIDIA GeForce RTX 5090", "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404"),
    ("NVIDIA A40", "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404"),
    ("NVIDIA A100-SXM4-80GB", "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404"),
    ("NVIDIA H100 80GB HBM3", "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404"),
    ("NVIDIA RTX PRO 6000 Blackwell Server Edition MIG 1g.24gb", "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404"),
]

CLOUDS = ["COMMUNITY", "SECURE"]


def delete_pod(token: str, pod_id: str) -> None:
    status, payload = http_json(
        f"https://rest.runpod.io/v1/pods/{pod_id}", token, method="DELETE"
    )
    print(f"  deleted {pod_id} status={status}", flush=True)


def probe_one(token: str, pubkey: str, gpu: str, image: str, cloud: str) -> dict:
    body = {
        "name": "sft-capacity-probe",
        "gpuTypeIds": [gpu],
        "gpuCount": 1,
        "containerDiskInGb": 75,
        "volumeInGb": 0,
        "ports": ["22/tcp"],
        "env": pod_env(pubkey),
        "supportPublicIp": True,
        "interruptible": False,
        "computeType": "GPU",
        "networkVolumeId": NETWORK_VOLUME,
        "volumeMountPath": "/workspace",
        "imageName": image,
        "cloudType": cloud,
        "dataCenterIds": [DATA_CENTER],
    }
    status, payload = http_json(
        "https://rest.runpod.io/v1/pods", token, body, method="POST"
    )
    row = {
        "gpu": gpu.split()[-1],
        "cloud": cloud,
        "http_status": status,
        "available": status in (200, 201),
    }
    if isinstance(payload, dict):
        if payload.get("id"):
            row["pod_id"] = payload["id"]
            row["error"] = None
        else:
            row["error"] = payload.get("detail") or payload.get("error") or str(payload)[:200]
    else:
        row["error"] = str(payload)[:200]
    return row


def main() -> int:
    token = load_mcp_token()
    pubkey = PUBKEY.read_text(encoding="utf-8").strip()
    results: list[dict] = []
    available: list[dict] = []

    print(f"Probing {DATA_CENTER} + volume {NETWORK_VOLUME} ...", flush=True)
    for gpu, image in CANDIDATES:
        for cloud in CLOUDS:
            row = probe_one(token, pubkey, gpu, image, cloud)
            results.append(row)
            tag = "OK" if row["available"] else "NO"
            err = row.get("error") or ""
            print(f"[{tag}] {row['gpu']} {cloud}: {err}", flush=True)
            if row["available"] and row.get("pod_id"):
                available.append(row)
                delete_pod(token, row["pod_id"])

    out = SCRIPT_DIR.parent / "kaggle" / "sft_usil1_capacity_probe.json"
    out.write_text(json.dumps({"results": results, "available": available}, indent=2), encoding="utf-8")
    print(f"\nWrote {out}", flush=True)

    if available:
        print("\nAVAILABLE NOW (pod deleted after probe):")
        for r in available:
            print(f"  {r['gpu']} {r['cloud']} pod={r.get('pod_id')}")
        return 0

    print("\nNo GPU type could be provisioned in US-IL-1 with volume right now.", flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
