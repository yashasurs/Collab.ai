"""
Tunnel management router.

Uses TunnelBroker for lifecycle management with per-user quotas,
idle timeouts, and automatic orphan cleanup.
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from app.schemas.schemas import CreateTunnelRequest
from app.services.tunnel_broker import tunnel_broker
from app.auth.dependencies import get_current_user
from app.models.models import User, Session as SessionModel
from app.database.database import get_db
from sqlalchemy.orm import Session as DBSession
from app.services.orchestrator.factory import orchestrator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/create")
async def create_tunnel(
    req: CreateTunnelRequest, 
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Create a tunnel with quota enforcement."""
    session = db.query(SessionModel).filter(SessionModel.id == req.sessionId).first()
    if not session or not session.container_id:
        raise HTTPException(status_code=404, detail="Session or container not found")
        
    container_ip = "127.0.0.1"
    try:
        container_info = await orchestrator.get(session.container_id)
        if container_info.ip_address:
            container_ip = container_info.ip_address
    except Exception as e:
        logger.warning(f"Could not fetch container IP: {e}")

    try:
        info = await tunnel_broker.create_tunnel(
            session_id=req.sessionId,
            user_id=current_user.id,
            local_port=req.localPort,
            container_ip=container_ip,
        )
        return {
            "success": True,
            "sessionId": info.session_id,
            "tunnelUrl": info.url,
        }
    except RuntimeError as e:
        if "quota exceeded" in str(e).lower():
            raise HTTPException(status_code=429, detail=str(e))
        elif "not found" in str(e).lower():
            raise HTTPException(status_code=503, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_tunnels(current_user: User = Depends(get_current_user)):
    """List all active tunnels."""
    tunnels = await tunnel_broker.list_tunnels()
    return {
        "success": True,
        "tunnels": [
            {
                "sessionId": t.session_id,
                "url": t.url,
                "localPort": t.local_port,
                "userId": t.user_id,
                "createdAt": t.created_at,
            }
            for t in tunnels
        ],
    }


@router.get("/health")
async def tunnels_health():
    """Health check for the tunnel subsystem."""
    tunnels = await tunnel_broker.list_tunnels()
    healthy = 0
    for t in tunnels:
        if await tunnel_broker.health_check(t.session_id):
            healthy += 1
    return {
        "success": True,
        "total": len(tunnels),
        "healthy": healthy,
        "maxPerUser": tunnel_broker.__class__.__module__ and 3,  # MAX_TUNNELS_PER_USER
    }


@router.get("/{session_id}")
async def get_tunnel(session_id: str, current_user: User = Depends(get_current_user)):
    """Get tunnel info for a specific session."""
    info = await tunnel_broker.get_tunnel(session_id)
    if not info:
        raise HTTPException(status_code=404, detail="No active tunnel for this session")
    return {
        "success": True,
        "sessionId": session_id,
        "tunnelUrl": info.url,
        "localPort": info.local_port,
    }


@router.delete("/{session_id}")
async def close_tunnel(session_id: str, current_user: User = Depends(get_current_user)):
    """Close a tunnel."""
    closed = await tunnel_broker.close_tunnel(session_id)
    if not closed:
        raise HTTPException(status_code=404, detail="No active tunnel for this session")
    return {"success": True, "message": f"Tunnel for session {session_id} closed"}
