from fastapi import APIRouter, HTTPException
import subprocess
import re
import logging
import time
from typing import Dict

from app.schemas.schemas import CreateTunnelRequest

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory store for active tunnel processes
# Key: session_id, Value: {"process": Popen, "url": str, "localPort": int}
_active_tunnels: Dict[str, dict] = {}

TUNNEL_URL_PATTERN = re.compile(r"https://[a-z0-9\-]+\.trycloudflare\.com")


@router.post("/create")
async def create_tunnel(req: CreateTunnelRequest):
    if req.sessionId in _active_tunnels:
        existing = _active_tunnels[req.sessionId]
        return {"success": True, "sessionId": req.sessionId, "tunnelUrl": existing["url"]}

    local_url = f"http://localhost:{req.localPort}"
    try:
        proc = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", local_url],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="cloudflared not found. Install it from https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
        )

    # Wait up to 10s for the tunnel URL to appear in output
    tunnel_url = None
    deadline = time.time() + 10
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            break
        match = TUNNEL_URL_PATTERN.search(line)
        if match:
            tunnel_url = match.group(0)
            break

    if not tunnel_url:
        proc.terminate()
        raise HTTPException(status_code=500, detail="Timed out waiting for cloudflared tunnel URL")

    _active_tunnels[req.sessionId] = {
        "process": proc,
        "url": tunnel_url,
        "localPort": req.localPort,
    }
    logger.info(f"Tunnel created for session {req.sessionId}: {tunnel_url}")
    return {"success": True, "sessionId": req.sessionId, "tunnelUrl": tunnel_url}


@router.get("/")
async def list_tunnels():
    return {
        "success": True,
        "tunnels": [
            {"sessionId": sid, "url": info["url"], "localPort": info["localPort"]}
            for sid, info in _active_tunnels.items()
        ],
    }


@router.get("/{session_id}")
async def get_tunnel(session_id: str):
    info = _active_tunnels.get(session_id)
    if not info:
        raise HTTPException(status_code=404, detail="No active tunnel for this session")
    return {"success": True, "sessionId": session_id, "tunnelUrl": info["url"], "localPort": info["localPort"]}


@router.delete("/{session_id}")
async def close_tunnel(session_id: str):
    info = _active_tunnels.pop(session_id, None)
    if not info:
        raise HTTPException(status_code=404, detail="No active tunnel for this session")
    proc = info["process"]
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    logger.info(f"Tunnel closed for session {session_id}")
    return {"success": True, "message": f"Tunnel for session {session_id} closed"}
