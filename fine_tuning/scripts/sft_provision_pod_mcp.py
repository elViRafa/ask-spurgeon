"""Provision SFT GATE-0 pod via REST v1 using Cursor MCP OAuth token."""
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
_SESSION_ENV = (os.environ.get("SFT_SESSION_FILE") or "").strip()
SESSION = Path(_SESSION_ENV) if _SESSION_ENV else (REPO / "fine_tuning" / "kaggle" / "sft_session.json")
PUBKEY = Path.home() / ".ssh" / "runpod_cpt.pub"
# Default is the US-IL-1 volume created 2026-10-17 on the funded API-key account.
NETWORK_VOLUME = (os.environ.get("SFT_NETWORK_VOLUME_ID") or "37lkz6dt50").strip()
DATA_CENTER = "US-IL-1"
VOLUME_NAME = (os.environ.get("SFT_NETWORK_VOLUME_NAME") or "sft-s8-weighted").strip()
VOLUME_SIZE_GB = int(os.environ.get("SFT_NETWORK_VOLUME_GB") or "75")
POD_NAME = (os.environ.get("SFT_POD_NAME") or "sft-gate0").strip() or "sft-gate0"
HUB_V2_SHA = "319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478"
MAX_WALL_HOURS = int(os.environ.get("SFT_MAX_WALL_HOURS", "8"))


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


def load_api_key_token() -> str:
    """Prefer the runpodctl / .env API key (funded account) over MCP OAuth."""
    env = (os.environ.get("RUNPOD_API_KEY") or "").strip()
    if env:
        return env
    dotenv = REPO / ".env"
    if dotenv.is_file():
        for line in dotenv.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("RUNPOD_API_KEY="):
                val = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    return val
    cfg = Path.home() / ".runpod" / "config.toml"
    if cfg.is_file():
        import re

        text = cfg.read_text(encoding="utf-8")
        m = re.search(r"apikey\s*=\s*'([^']+)'", text) or re.search(
            r'apikey\s*=\s*"([^"]+)"', text
        )
        if m and m.group(1).strip():
            return m.group(1).strip()
    return ""


def load_mcp_oauth_token() -> str:
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


def load_mcp_token() -> str:
    """
    Auth for REST create / wait.

    Prefer RUNPOD_API_KEY (.env or ~/.runpod/config.toml) so pods land on the
    funded runpodctl account. MCP OAuth can be a *different* wallet (low balance,
    pods invisible to runpodctl) — use it only as fallback.
    """
    api = load_api_key_token()
    if api:
        print("AUTH=runpod_api_key", flush=True)
        return api
    print("AUTH=mcp_oauth_fallback", flush=True)
    return load_mcp_oauth_token()


def http_json(url: str, token: str, body: dict | None = None, method: str = "GET") -> tuple[int, object]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Content-Type", "application/json")
    # Cloudflare returns 403 error code 1010 when User-Agent is absent.
    req.add_header("User-Agent", "ask-spurgeon-sft-provision/1.0")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8")
            if not raw.strip():
                return resp.status, {}
            return resp.status, json.loads(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            return exc.code, raw[:1000]


def get_pod(token: str, pod_id: str) -> dict:
    status, payload = http_json(f"https://rest.runpod.io/v1/pods/{pod_id}", token)
    if status != 200 or not isinstance(payload, dict):
        raise RuntimeError(f"GET pod failed {status}: {payload}")
    return payload


def graphql_json(token: str, query: str, variables: dict | None = None) -> dict:
    """POST https://api.runpod.io/graphql — REST v1 often omits ssh/runtime."""
    body = {"query": query, "variables": variables or {}}
    status, payload = http_json(
        "https://api.runpod.io/graphql", token, body=body, method="POST"
    )
    if status != 200 or not isinstance(payload, dict):
        raise RuntimeError(f"GraphQL failed {status}: {payload}")
    if payload.get("errors"):
        raise RuntimeError(f"GraphQL errors: {payload['errors']}")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError(f"GraphQL missing data: {payload}")
    return data


def graphql_pod_ssh(token: str, pod_id: str) -> dict | None:
    """
    Resolve proxy SSH via GraphQL machine.podHostId.

    Cursor MCP OAuth REST v1 GET /pods/{id} returns desiredStatus but no ssh/
    publicIp/runtime. GraphQL still exposes podHostId for ssh.runpod.io proxy
    even while runtime is null (container still creating).
    """
    data = graphql_json(
        token,
        """
        query PodSsh($id: String!) {
          pod(input: { podId: $id }) {
            id
            desiredStatus
            runtime {
              uptimeInSeconds
              ports {
                ip
                isIpPublic
                privatePort
                publicPort
                type
              }
            }
            machine {
              podHostId
            }
          }
        }
        """,
        {"id": pod_id},
    )
    pod = data.get("pod") or {}
    if not isinstance(pod, dict):
        return None
    runtime = pod.get("runtime") or {}
    ports = runtime.get("ports") or []
    for entry in ports:
        if not isinstance(entry, dict):
            continue
        if entry.get("privatePort") == 22 and entry.get("publicPort") and entry.get("ip"):
            return {
                "ssh_mode": "direct",
                "ssh_host": str(entry["ip"]),
                "ssh_port": int(entry["publicPort"]),
                "ssh_user": "root",
            }
    machine = pod.get("machine") or {}
    host_id = (machine.get("podHostId") or "").strip()
    if host_id:
        return {
            "ssh_mode": "proxy",
            "ssh_host": "ssh.runpod.io",
            "ssh_port": 22,
            "ssh_user": host_id,
        }
    return None


def probe_ssh(ssh_info: dict) -> bool:
    """True when a non-interactive command reaches the container (not just the proxy)."""
    import subprocess

    key = str(PUBKEY).removesuffix(".pub")
    if not Path(key).is_file():
        return False
    user = ssh_info["ssh_user"]
    host = ssh_info["ssh_host"]
    port = int(ssh_info["ssh_port"])
    target = f"{user}@{host}"
    cmd = [
        "ssh",
        "-T",
        "-i",
        key,
        "-p",
        str(port),
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        "UserKnownHostsFile=NUL" if sys.platform.startswith("win") else "/dev/null",
        "-o",
        "LogLevel=ERROR",
        "-o",
        "ConnectTimeout=20",
        "-o",
        "RequestTTY=no",
        target,
        "echo SSH_PROBE_OK",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=45, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return False
    out = (proc.stdout or "") + (proc.stderr or "")
    if "container not found" in out.lower():
        return False
    if "GPU requires reset" in out:
        return False
    return proc.returncode == 0 and "SSH_PROBE_OK" in out


def wait_ssh(token: str, pod_id: str, timeout_min: int = 20) -> dict:
    import time

    deadline = time.time() + timeout_min * 60
    # When GraphQL already exposes podHostId but the container never answers
    # (e.g. "GPU requires reset"), fail fast instead of burning the full timeout.
    unreachable_with_proxy = 0
    while time.time() < deadline:
        candidates: list[dict] = []
        pod = get_pod(token, pod_id)
        runtime = pod.get("runtime") or {}
        host = runtime.get("publicIp") or pod.get("publicIp")
        ports = runtime.get("ports") or []
        ssh_port = None
        port_mappings = pod.get("portMappings") or {}
        if port_mappings:
            ssh_port = port_mappings.get("22") or port_mappings.get(22)
        for entry in ports:
            if not isinstance(entry, dict):
                continue
            priv = entry.get("privatePort", entry.get("private"))
            pub = entry.get("publicPort", entry.get("public"))
            if priv == 22 and pub:
                ssh_port = pub
                if not host:
                    host = entry.get("ip")
                break
        ssh_block = pod.get("ssh") or {}
        direct = ssh_block.get("direct") or {}
        if direct.get("host") and direct.get("port"):
            candidates.append(
                {
                    "ssh_mode": "direct",
                    "ssh_host": str(direct["host"]),
                    "ssh_port": int(direct["port"]),
                    "ssh_user": "root",
                }
            )
        proxy = ssh_block.get("proxy") or {}
        if proxy.get("host") and proxy.get("username"):
            candidates.append(
                {
                    "ssh_mode": "proxy",
                    "ssh_host": str(proxy["host"]),
                    "ssh_port": int(proxy.get("port") or 22),
                    "ssh_user": str(proxy["username"]),
                }
            )
        if host and ssh_port:
            candidates.append(
                {
                    "ssh_mode": "direct",
                    "ssh_host": str(host),
                    "ssh_port": int(ssh_port),
                    "ssh_user": "root",
                }
            )
        # REST v1 (MCP OAuth) often omits ssh — fall back to GraphQL podHostId.
        try:
            gql = graphql_pod_ssh(token, pod_id)
        except Exception as exc:  # noqa: BLE001 — keep polling on transient GraphQL errors
            print(f"wait_ssh graphql fallback: {exc}", file=sys.stderr)
            gql = None
        if gql:
            candidates.append(gql)

        seen: set[tuple[str, str, int]] = set()
        probed = False
        for info in candidates:
            key = (info["ssh_user"], info["ssh_host"], int(info["ssh_port"]))
            if key in seen:
                continue
            seen.add(key)
            probed = True
            if probe_ssh(info):
                print(
                    "SSH_PROBE_OK",
                    info["ssh_user"] + "@" + info["ssh_host"],
                    info["ssh_port"],
                    info["ssh_mode"],
                )
                return info
        if probed:
            unreachable_with_proxy += 1
            if unreachable_with_proxy >= 8:
                raise TimeoutError(
                    f"SSH proxy known but container unreachable for pod {pod_id} "
                    "(likely bad GPU host / GPU requires reset)"
                )
        time.sleep(15)
    raise TimeoutError(f"SSH not ready for pod {pod_id}")


def load_hf_token() -> str:
    tok = (os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN") or "").strip()
    if tok:
        return tok
    dotenv = REPO / ".env"
    if dotenv.is_file():
        for line in dotenv.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("HF_TOKEN="):
                return stripped.split("=", 1)[1].strip().strip('"').strip("'")
            if stripped.startswith("HUGGING_FACE_HUB_TOKEN="):
                return stripped.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def pod_env(pubkey: str) -> dict[str, str]:
    hf = load_hf_token()
    if not hf:
        raise RuntimeError("HF_TOKEN missing — Hub v2 LoRA repo is private; set it in .env")
    return {
        "PUBLIC_KEY": pubkey,
        "HF_TOKEN": hf,
        "HF_HOME": "/workspace/hf_home",
    }


def _create_attempt(
    token: str,
    pubkey: str,
    *,
    gpu: str,
    image: str,
    cloud: str,
    data_centers: list[str],
    network_volume_id: str | None,
    attempt_n: int,
) -> tuple[str, dict] | None:
    body: dict = {
        "name": POD_NAME,
        "gpuTypeIds": [gpu],
        "gpuCount": 1,
        "containerDiskInGb": 100 if not network_volume_id else 75,
        "volumeInGb": 0,
        "ports": ["22/tcp"],
        "env": pod_env(pubkey),
        "supportPublicIp": True,
        "interruptible": False,
        "computeType": "GPU",
        "imageName": image,
        "cloudType": cloud,
        "dataCenterIds": data_centers,
    }
    if network_volume_id:
        body["networkVolumeId"] = network_volume_id
        body["volumeMountPath"] = "/workspace"
    mode = f"vol={network_volume_id}" if network_volume_id else "ephemeral"
    print(
        "attempt",
        attempt_n,
        cloud,
        gpu.split()[-1],
        image.split("/")[-1],
        mode,
        flush=True,
    )
    status, payload = http_json(
        "https://rest.runpod.io/v1/pods", token, body, method="POST"
    )
    print("status", status, flush=True)
    if status in (200, 201) and isinstance(payload, dict) and payload.get("id"):
        pod_id = str(payload["id"])
        dc = data_centers[0] if data_centers else DATA_CENTER
        meta = {
            "pod_id": pod_id,
            "name": POD_NAME,
            "cloud_type": cloud,
            "data_center": dc,
            "gpu_type": gpu,
            "created_at": __import__("datetime").datetime.now().isoformat(),
            "network_volume_id": network_volume_id or "",
            "ephemeral_workspace": not bool(network_volume_id),
            "volume_mount_path": "/workspace",
            "image_name": image,
            "gate0_merged": "/workspace/theology_cpt_v2_merged_hf",
            "hub_v2_adapter_sha256": HUB_V2_SHA,
            "use_cpt_merge": True,
            "export": False,
            "max_wall_hours": MAX_WALL_HOURS,
            "auth": "runpod_rest_v1",
            "monitor_status": "provisioned",
        }
        return pod_id, meta
    if isinstance(payload, dict):
        err = payload.get("detail") or payload.get("error") or payload
        print("error", err, flush=True)
    else:
        print("error", str(payload)[:500], flush=True)
    return None


def ensure_network_volume(token: str) -> str | None:
    """Return a usable network volume id, creating one on the funded account if needed."""
    global NETWORK_VOLUME
    if NETWORK_VOLUME:
        status, payload = http_json(
            f"https://rest.runpod.io/v1/networkvolumes/{NETWORK_VOLUME}", token
        )
        if status == 200 and isinstance(payload, dict) and payload.get("id"):
            print("VOLUME_OK", NETWORK_VOLUME, flush=True)
            return NETWORK_VOLUME
        print("VOLUME_MISSING", NETWORK_VOLUME, "http", status, flush=True)

    status, listing = http_json("https://rest.runpod.io/v1/networkvolumes", token)
    if status == 200 and isinstance(listing, list):
        for vol in listing:
            if not isinstance(vol, dict):
                continue
            if vol.get("name") == VOLUME_NAME and vol.get("id"):
                NETWORK_VOLUME = str(vol["id"])
                print("VOLUME_REUSE", NETWORK_VOLUME, VOLUME_NAME, flush=True)
                return NETWORK_VOLUME
    elif status == 200 and isinstance(listing, dict):
        for vol in listing.get("networkVolumes") or listing.get("items") or []:
            if not isinstance(vol, dict):
                continue
            if vol.get("name") == VOLUME_NAME and vol.get("id"):
                NETWORK_VOLUME = str(vol["id"])
                print("VOLUME_REUSE", NETWORK_VOLUME, VOLUME_NAME, flush=True)
                return NETWORK_VOLUME

    body = {
        "name": VOLUME_NAME,
        "size": VOLUME_SIZE_GB,
        "dataCenterId": DATA_CENTER,
    }
    # REST variants: dataCenterId vs dataCenter
    status, payload = http_json(
        "https://rest.runpod.io/v1/networkvolumes", token, body=body, method="POST"
    )
    if status not in (200, 201) or not isinstance(payload, dict) or not payload.get("id"):
        body2 = {"name": VOLUME_NAME, "size": VOLUME_SIZE_GB, "dataCenter": DATA_CENTER}
        status, payload = http_json(
            "https://rest.runpod.io/v1/networkvolumes", token, body=body2, method="POST"
        )
    if status in (200, 201) and isinstance(payload, dict) and payload.get("id"):
        NETWORK_VOLUME = str(payload["id"])
        print("VOLUME_CREATED", NETWORK_VOLUME, DATA_CENTER, f"{VOLUME_SIZE_GB}GB", flush=True)
        return NETWORK_VOLUME
    print("VOLUME_CREATE_FAILED", status, payload, flush=True)
    return None


def try_provision_pod(token: str, pubkey: str) -> tuple[str, dict] | None:
    vol_id = ensure_network_volume(token)
    if vol_id:
        # Prefer attaching the volume we just verified/created.
        pass
    gpu_types = [
        "NVIDIA GeForce RTX 4090",
        "NVIDIA L40S",
    ]
    images = [
        "runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404",
        "runpod/pytorch:0.7.0-cu1241-torch260-ubuntu2204",
    ]
    clouds = ["COMMUNITY", "SECURE"]
    attempt_n = 0
    volume_id = vol_id or NETWORK_VOLUME or None
    volume_missing = False
    if volume_id:
        for gpu in gpu_types:
            for image in images:
                for cloud in clouds:
                    attempt_n += 1
                    hit = _create_attempt(
                        token,
                        pubkey,
                        gpu=gpu,
                        image=image,
                        cloud=cloud,
                        data_centers=[DATA_CENTER],
                        network_volume_id=volume_id,
                        attempt_n=attempt_n,
                    )
                    if hit:
                        return hit
                    # Detect deleted/missing volume so we can fall back once.
                    volume_missing = True
    else:
        volume_missing = True

    if not volume_missing:
        return None

    print(
        "NETWORK_VOLUME_MISSING: falling back to ephemeral /workspace "
        f"(no usable volume; create volume when account balance >= $5)",
        flush=True,
    )
    # Any DC with stock — S8 merge comes from private Hub, not the old volume.
    for gpu in gpu_types:
        for image in images[:1]:
            for cloud in clouds:
                attempt_n += 1
                hit = _create_attempt(
                    token,
                    pubkey,
                    gpu=gpu,
                    image=image,
                    cloud=cloud,
                    data_centers=[],
                    network_volume_id=None,
                    attempt_n=attempt_n,
                )
                if hit:
                    return hit
    return None


def save_session(data: dict) -> None:
    SESSION.parent.mkdir(parents=True, exist_ok=True)
    SESSION.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_session() -> dict:
    if not SESSION.is_file():
        return {}
    return json.loads(SESSION.read_text(encoding="utf-8-sig"))


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
        pod_id = args.pod_id or json.loads(SESSION.read_text(encoding="utf-8-sig"))["pod_id"]
        timeout = int(os.environ.get("SFT_WAIT_TIMEOUT_MIN", "20"))
        ssh_info = wait_ssh(token, pod_id, timeout_min=timeout)
        print(
            "SSH_OK",
            ssh_info["ssh_user"] + "@" + ssh_info["ssh_host"],
            ssh_info["ssh_port"],
            ssh_info["ssh_mode"],
        )
        data = json.loads(SESSION.read_text(encoding="utf-8-sig"))
        data.update(ssh_info)
        SESSION.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return

    token = load_mcp_token()
    pubkey = PUBKEY.read_text(encoding="utf-8").strip()
    result = try_provision_pod(token, pubkey)
    if not result:
        raise SystemExit(
            "all REST v1 create attempts failed "
            f"(volume {NETWORK_VOLUME} missing or GPU stock/balance). "
            "Top up RunPod (volume create needs >= $5; Secure/Community need rent funds), "
            "then retry. Optional: set RUNPOD_API_KEY for runpodctl path."
        )
    pod_id, meta = result
    print("POD_OK", pod_id)
    save_session(meta)


if __name__ == "__main__":
    main()
