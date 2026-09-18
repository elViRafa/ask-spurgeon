"""Provision S6 continue-B pod via REST v1 using Cursor MCP OAuth token.

MCP create-pod 400s on objectMounts; REST v1 works with the same OAuth bearer.
Never print secrets. Writes pod id to continued_pretrain/kaggle/runpod_cpt_v3/s6_session.json.
"""
from __future__ import annotations

import base64
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from ctypes import POINTER, Structure, byref, c_byte, cast, create_string_buffer, string_at, windll, wintypes
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SESSION = REPO / "continued_pretrain" / "kaggle" / "runpod_cpt_v3" / "s6_session.json"
PUBKEY = Path.home() / ".ssh" / "runpod_cpt.pub"
NETWORK_VOLUME = "7hb931c5oe"
DATA_CENTER = "US-IL-1"
MAX_WALL_HOURS = int(os.environ.get("S6_MAX_WALL_HOURS", "16"))


class DATA_BLOB(Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", POINTER(c_byte))]


def dpapi_decrypt(data: bytes) -> bytes:
    buf = create_string_buffer(data, len(data))
    blob_in = DATA_BLOB(len(data), cast(buf, POINTER(c_byte)))
    blob_out = DATA_BLOB()
    ok = windll.crypt32.CryptUnprotectData(
        byref(blob_in), None, None, None, None, 0, byref(blob_out)
    )
    if not ok:
        raise RuntimeError(f"DPAPI failed err={windll.kernel32.GetLastError()}")
    out = string_at(blob_out.pbData, blob_out.cbData)
    windll.kernel32.LocalFree(blob_out.pbData)
    return out


def chrome_v10_decrypt(raw: bytes) -> bytes:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    state_paths = [
        Path(os.environ["APPDATA"]) / "Cursor" / "Local State",
        Path(os.environ["LOCALAPPDATA"]) / "Cursor" / "User" / "Local State",
    ]
    state_file = next((p for p in state_paths if p.is_file()), None)
    if state_file is None:
        raise FileNotFoundError("Cursor Local State not found")
    local_state = json.loads(state_file.read_text(encoding="utf-8"))
    enc_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    if enc_key.startswith(b"DPAPI"):
        enc_key = enc_key[5:]
    aes_key = dpapi_decrypt(enc_key)
    payload = raw[3:]
    return AESGCM(aes_key).decrypt(payload[:12], payload[12:], None)


def load_mcp_token() -> str:
    db = Path(os.environ["APPDATA"]) / "Cursor" / "User" / "globalStorage" / "state.vscdb"
    con = sqlite3.connect(str(db))
    row = con.execute(
        "SELECT value FROM ItemTable WHERE key LIKE 'mcpOAuth.secret.%' "
        "AND key LIKE '%cnVucG9k%' AND key LIKE '%b2tlbnM'"
    ).fetchone()
    if not row:
        raise RuntimeError("Runpod MCP OAuth token not found — sign in to Runpod MCP in Cursor")
    obj = json.loads(row[0])
    raw = bytes(obj["data"])
    decrypted = chrome_v10_decrypt(raw) if raw.startswith(b"v10") else raw
    parsed = json.loads(decrypted.decode("utf-8"))
    return str(parsed["access_token"])


def http_json(url: str, token: str, body: dict | None = None, method: str = "GET") -> tuple[int, object]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw[:1000]


def get_pod(token: str, pod_id: str) -> dict:
    status, payload = http_json(f"https://rest.runpod.io/v1/pods/{pod_id}", token)
    if status != 200 or not isinstance(payload, dict):
        raise RuntimeError(f"GET pod failed {status}: {payload}")
    return payload


def wait_ssh(token: str, pod_id: str, timeout_min: int = 20) -> dict:
    import time

    deadline = time.time() + timeout_min * 60
    while time.time() < deadline:
        pod = get_pod(token, pod_id)
        runtime = pod.get("runtime") or {}
        host = runtime.get("publicIp") or pod.get("publicIp")
        ports = runtime.get("ports") or []
        ssh_port = None
        port_mappings = pod.get("portMappings") or {}
        if port_mappings:
            ssh_port = port_mappings.get("22") or port_mappings.get(22)
        for entry in ports:
            priv = entry.get("privatePort", entry.get("private"))
            pub = entry.get("publicPort", entry.get("public"))
            if priv == 22 and pub:
                ssh_port = pub
                if not host:
                    host = entry.get("ip")
                break
        if ssh_port is None and ports:
            ssh_port = ports[0].get("publicPort", ports[0].get("public"))
            if not host:
                host = ports[0].get("ip")
        ssh_block = pod.get("ssh") or {}
        direct = ssh_block.get("direct") or {}
        if direct.get("host") and direct.get("port"):
            return {
                "ssh_mode": "direct",
                "ssh_host": str(direct["host"]),
                "ssh_port": int(direct["port"]),
                "ssh_user": "root",
            }
        proxy = ssh_block.get("proxy") or {}
        if proxy.get("host") and proxy.get("username"):
            return {
                "ssh_mode": "proxy",
                "ssh_host": str(proxy["host"]),
                "ssh_port": int(proxy.get("port") or 22),
                "ssh_user": str(proxy["username"]),
            }
        if host and ssh_port:
            return {
                "ssh_mode": "direct",
                "ssh_host": str(host),
                "ssh_port": int(ssh_port),
                "ssh_user": "root",
            }
        time.sleep(15)
    raise TimeoutError(f"SSH not ready for pod {pod_id}")


def try_provision_pod(token: str, pubkey: str) -> tuple[str, dict] | None:
    """Create pod in US-IL-1 with volume. Returns (pod_id, session_meta) or None."""
    base = {
        "name": "s6-continue-b-cpt",
        "gpuTypeIds": ["NVIDIA GeForce RTX 4090"],
        "gpuCount": 1,
        "containerDiskInGb": 75,
        "volumeInGb": 0,
        "ports": ["22/tcp"],
        "env": {"PUBLIC_KEY": pubkey},
        "supportPublicIp": True,
        "interruptible": False,
        "computeType": "GPU",
        "networkVolumeId": NETWORK_VOLUME,
        "volumeMountPath": "/workspace",
    }
    attempts = [
        {
            **base,
            "imageName": "runpod/pytorch:0.7.0-cu1241-torch260-ubuntu2204",
            "cloudType": "COMMUNITY",
            "dataCenterIds": [DATA_CENTER],
        },
        {
            **base,
            "imageName": "runpod/pytorch:0.7.0-cu1241-torch260-ubuntu2204",
            "cloudType": "SECURE",
            "dataCenterIds": [DATA_CENTER],
        },
        {
            **base,
            "imageName": "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04",
            "cloudType": "SECURE",
            "dataCenterIds": [DATA_CENTER],
        },
        {
            **base,
            "imageName": "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404",
            "cloudType": "COMMUNITY",
            "dataCenterIds": [DATA_CENTER],
        },
        {
            **base,
            "imageName": "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404",
            "cloudType": "SECURE",
            "dataCenterIds": [DATA_CENTER],
        },
    ]
    for i, body in enumerate(attempts, 1):
        print(
            "attempt",
            i,
            body.get("cloudType"),
            body.get("dataCenterIds"),
            body.get("imageName"),
            flush=True,
        )
        status, payload = http_json("https://rest.runpod.io/v1/pods", token, body, method="POST")
        print("status", status, flush=True)
        if status in (200, 201) and isinstance(payload, dict) and payload.get("id"):
            pod_id = str(payload["id"])
            meta = {
                "pod_id": pod_id,
                "cloud_type": body.get("cloudType"),
                "data_center": DATA_CENTER,
                "created_at": __import__("datetime").datetime.now().isoformat(),
                "network_volume_id": NETWORK_VOLUME,
                "volume_mount_path": "/workspace",
                "image_name": body.get("imageName"),
                "max_wall_hours": MAX_WALL_HOURS,
                "auth": "mcp_oauth_rest_v1",
                "monitor_status": "provisioned",
            }
            return pod_id, meta
        if isinstance(payload, dict):
            print("error", payload.get("detail") or payload.get("error") or payload, flush=True)
        else:
            print("error", str(payload)[:500], flush=True)
    return None


def save_session(data: dict) -> None:
    SESSION.parent.mkdir(parents=True, exist_ok=True)
    SESSION.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_session() -> dict:
    if not SESSION.is_file():
        return {}
    return json.loads(SESSION.read_text(encoding="utf-8"))


def pod_exists(token: str, pod_id: str) -> bool:
    status, payload = http_json(f"https://rest.runpod.io/v1/pods/{pod_id}", token)
    return status == 200 and isinstance(payload, dict)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-ssh", action="store_true")
    parser.add_argument("--pod-id", default="")
    args = parser.parse_args()

    if args.wait_ssh:
        token = load_mcp_token()
        pod_id = args.pod_id or json.loads(SESSION.read_text(encoding="utf-8"))["pod_id"]
        timeout = int(os.environ.get("S6_WAIT_TIMEOUT_MIN", "20"))
        ssh_info = wait_ssh(token, pod_id, timeout_min=timeout)
        print(
            "SSH_OK",
            ssh_info["ssh_user"] + "@" + ssh_info["ssh_host"],
            ssh_info["ssh_port"],
            ssh_info["ssh_mode"],
        )
        data = json.loads(SESSION.read_text(encoding="utf-8"))
        data.update(ssh_info)
        SESSION.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return

    token = load_mcp_token()
    pubkey = PUBKEY.read_text(encoding="utf-8").strip()
    result = try_provision_pod(token, pubkey)
    if not result:
        raise SystemExit(
            "all REST v1 create attempts failed (US-IL-1 + volume 7hb931c5oe). "
            "Try again later or set RUNPOD_API_KEY and use runpodctl path in s6_provision_pod.ps1"
        )
    pod_id, meta = result
    print("POD_OK", pod_id)
    save_session(meta)


if __name__ == "__main__":
    main()
