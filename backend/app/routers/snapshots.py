from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session as DBSession
from typing import List
import uuid
import datetime

from app.database.database import get_db
from app.models.models import Snapshot, Session
from app.schemas.schemas import SnapshotOut, SnapshotCreate
import app.routers.containers as containers_router

router = APIRouter()

@router.get("/", response_model=List[SnapshotOut])
async def list_snapshots(db: DBSession = Depends(get_db)):
    snapshots = db.query(Snapshot).all()
    # Manual mapping for camelCase if needed, or use alias_generator in Pydantic
    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "dockerImage": s.docker_image,
            "createdAt": s.created_at
        }
        for s in snapshots
    ]

@router.post("/create")
async def create_snapshot(req: SnapshotCreate, db: DBSession = Depends(get_db)):
    # 1. Find the session and its container
    db_session = db.query(Session).filter(Session.id == req.sessionId).first()
    if not db_session or not db_session.container_id:
        raise HTTPException(status_code=404, detail="Active session or container not found")

    # 2. Call container snapshot logic (logic from containers.py)
    # Since we want to keep it simple, we'll just reuse the logic here or refactor
    import docker
    try:
        client = docker.from_env()
        container = client.containers.get(db_session.container_id)
        
        snapshot_id = str(uuid.uuid4())[:8]
        repository = f"colab-snapshot-{snapshot_id}"
        
        image = container.commit(
            repository=repository,
            tag="latest",
            message=req.description or "",
            author="colab.ai",
        )
        
        # 3. Save to database
        db_snapshot = Snapshot(
            id=snapshot_id,
            name=req.name,
            description=req.description,
            docker_image=repository
        )
        db.add(db_snapshot)
        db.commit()
        db.refresh(db_snapshot)
        
        return {"success": True, "snapshot": db_snapshot}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
