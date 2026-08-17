"""
Snapshot management router.

Uses the orchestrator interface for container snapshots,
and stores metadata in the database.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session as DBSession
from typing import List
import uuid
import logging

from app.database.database import get_db
from app.models.models import Snapshot, Session
from app.schemas.schemas import SnapshotOut, SnapshotCreate
from app.services.orchestrator.factory import orchestrator
from app.auth.dependencies import get_current_user
from app.models.models import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[SnapshotOut])
async def list_snapshots(db: DBSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List all available snapshots."""
    snapshots = db.query(Snapshot).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "dockerImage": s.docker_image,
            "createdAt": s.created_at,
        }
        for s in snapshots
    ]


@router.post("/create")
async def create_snapshot(
    req: SnapshotCreate,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a snapshot of a session's container."""
    # 1. Find the session and its container
    db_session = db.query(Session).filter(Session.id == req.sessionId).first()
    if not db_session or not db_session.container_id:
        raise HTTPException(status_code=404, detail="Active session or container not found")

    # 2. Create snapshot via orchestrator
    try:
        snapshot_info = await orchestrator.snapshot(
            container_id=db_session.container_id,
            name=req.name,
            description=req.description or "",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 3. Save metadata to database
    db_snapshot = Snapshot(
        id=snapshot_info.snapshot_id,
        name=req.name,
        description=req.description,
        docker_image=snapshot_info.snapshot_id,
    )
    db.add(db_snapshot)
    db.commit()
    db.refresh(db_snapshot)

    return {"success": True, "snapshot": db_snapshot}
