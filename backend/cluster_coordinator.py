import asyncio
import json
import logging
import os
import platform
import socket
import subprocess
import time
from typing import Dict, Any

logger = logging.getLogger("ClusterCoordinator")

ORACLE_VM_IP = os.getenv("ORACLE_VM_IP", "129.225.125.13")
ORACLE_VM_USER = os.getenv("ORACLE_VM_USER", "opc")
ORACLE_SSH_KEY = os.path.expanduser(os.getenv("ORACLE_SSH_KEY", "~/.ssh/oracle_tradeverse.key"))
LEASE_FILE = "/tmp/tradeverse_imac_lease.json"
DEFAULT_LEASE_TTL_SECONDS = 45
HEARTBEAT_INTERVAL_SECONDS = 15

IS_IMAC_NODE = (
    platform.system() == "Darwin"
    and os.getenv("TRADEVERSE_FORCE_CLOUD_ROLE", "").lower() not in ("1", "true", "yes")
)
IS_CLOUD_NODE = not IS_IMAC_NODE

_imac_beacon_state: Dict[str, Any] = {
    "last_sent_ts": 0.0,
    "last_ok": False,
    "consecutive_failures": 0,
}


def read_imac_lease() -> Dict[str, Any]:
    """Reads the iMac heartbeat lease file on the Cloud VM."""
    if not IS_CLOUD_NODE:
        return {"active": True, "node": "iMac", "remaining_seconds": DEFAULT_LEASE_TTL_SECONDS}

    if not os.path.exists(LEASE_FILE):
        return {"active": False, "node": None, "remaining_seconds": 0.0}

    try:
        with open(LEASE_FILE, "r") as f:
            raw = f.read().strip()
        if not raw:
            return {"active": False, "node": None, "remaining_seconds": 0.0}
        data = json.loads(raw) if raw.startswith("{") else {"ts": float(raw), "ttl": DEFAULT_LEASE_TTL_SECONDS}
        ts = float(data.get("ts", 0.0))
        ttl = float(data.get("ttl", DEFAULT_LEASE_TTL_SECONDS))
        age = time.time() - ts
        remaining = max(0.0, ttl - age)
        return {
            "active": age < ttl,
            "node": data.get("host", "iMac"),
            "last_heartbeat_age_s": round(age, 1),
            "remaining_seconds": round(remaining, 1),
        }
    except Exception:
        return {"active": False, "node": None, "remaining_seconds": 0.0}


def is_cloud_standby() -> bool:
    """
    Returns True ONLY on the Cloud VM while the iMac heartbeat lease is fresh (< 45s old).
    When iMac shuts down, sleeps, or disconnects for >= 45s, returns False so Cloud auto-promotes to Primary.
    """
    if not IS_CLOUD_NODE:
        return False
    return bool(read_imac_lease().get("active", False))


def get_cluster_status() -> Dict[str, Any]:
    if IS_IMAC_NODE:
        return {
            "node": "IMAC_LOCAL",
            "role": "IMAC_PRIMARY",
            "cloud_vm": ORACLE_VM_IP,
            "cloud_standby_synced": _imac_beacon_state["last_ok"],
            "last_beacon_ts": _imac_beacon_state["last_sent_ts"],
            "failover_ttl_seconds": DEFAULT_LEASE_TTL_SECONDS,
        }
    lease = read_imac_lease()
    return {
        "node": "ORACLE_CLOUD_VM",
        "role": "HOT_STANDBY" if lease["active"] else "CLOUD_PRIMARY",
        "imac_lease": lease,
        "failover_ttl_seconds": DEFAULT_LEASE_TTL_SECONDS,
    }


async def send_imac_lease_once() -> bool:
    """Sends a 15s heartbeat lease from iMac to Oracle Cloud VM over SSH."""
    if not IS_IMAC_NODE or not os.path.exists(ORACLE_SSH_KEY):
        return False

    host = socket.gethostname() or "iMac"
    remote_cmd = (
        f'printf \'{{"ts":%s,"host":"{host}","ttl":{DEFAULT_LEASE_TTL_SECONDS}}}\\n\' '
        f'"$(date +%s)" > {LEASE_FILE}.tmp && mv -f {LEASE_FILE}.tmp {LEASE_FILE}'
    )
    try:
        proc = await asyncio.create_subprocess_exec(
            "ssh",
            "-i", ORACLE_SSH_KEY,
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=5",
            "-o", "ServerAliveInterval=5",
            "-o", "StrictHostKeyChecking=no",
            f"{ORACLE_VM_USER}@{ORACLE_VM_IP}",
            remote_cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            rc = await asyncio.wait_for(proc.wait(), timeout=8.0)
        except asyncio.TimeoutError:
            proc.kill()
            rc = -1

        ok = rc == 0
        _imac_beacon_state["last_sent_ts"] = time.time()
        _imac_beacon_state["last_ok"] = ok
        _imac_beacon_state["consecutive_failures"] = 0 if ok else _imac_beacon_state["consecutive_failures"] + 1
        return ok
    except Exception as e:
        logger.debug(f"iMac lease beacon warning: {e}")
        _imac_beacon_state["last_ok"] = False
        _imac_beacon_state["consecutive_failures"] += 1
        return False


def release_imac_lease_sync() -> None:
    """Immediately clears the lease on clean iMac exit/shutdown so Cloud takes over in <1s."""
    if not IS_IMAC_NODE or not os.path.exists(ORACLE_SSH_KEY):
        return
    try:
        subprocess.run(
            [
                "ssh",
                "-i", ORACLE_SSH_KEY,
                "-o", "BatchMode=yes",
                "-o", "ConnectTimeout=3",
                "-o", "StrictHostKeyChecking=no",
                f"{ORACLE_VM_USER}@{ORACLE_VM_IP}",
                f"rm -f {LEASE_FILE} {LEASE_FILE}.tmp",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=4,
        )
        logger.info("☁️ Released iMac cluster lease — Oracle Cloud VM promoted immediately.")
    except Exception:
        pass


async def run_imac_heartbeat_beacon() -> None:
    """Continuous background daemon on iMac keeping Oracle Cloud in Hot Standby while iMac is ON."""
    if not IS_IMAC_NODE:
        return
    logger.info(
        f"💓 [Cluster] Starting iMac Primary Heartbeat Beacon -> Oracle Cloud ({ORACLE_VM_IP}) every {HEARTBEAT_INTERVAL_SECONDS}s (TTL={DEFAULT_LEASE_TTL_SECONDS}s)"
    )
    while True:
        await send_imac_lease_once()
        await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
