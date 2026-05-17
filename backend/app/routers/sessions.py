from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session as DBSession
import uuid
import datetime

from app.database.database import get_db
from app.models.models import Session, Participant
from app.schemas.schemas import CreateSessionRequest, ParticipantCreate


router = APIRouter()


OS_OPTIONS = [
    {"id": "alpine",  "name": "Alpine Linux",  "description": "Lightweight (~5MB)",              "icon": "🏔️"},
    {"id": "ubuntu",  "name": "Ubuntu 22.04",   "description": "Popular & Beginner-friendly",     "icon": "🟠"},
    {"id": "debian",  "name": "Debian 12",      "description": "Stable & Reliable",               "icon": "🔴"},
    {"id": "fedora",  "name": "Fedora 39",      "description": "Modern & Cutting-edge",           "icon": "🔵"},
    {"id": "arch",    "name": "Arch Linux",     "description": "Rolling Release",                 "icon": "⚫"},
]


# ── Must be registered before /{session_id} so FastAPI doesn't shadow it ──────

@router.get("")
@router.get("/")
async def list_sessions(db: DBSession = Depends(get_db)):
    db_sessions = db.query(Session).all()
    return [_session_to_dict(s) for s in db_sessions]


@router.get("/os-options")
async def get_os_options():
    return {"success": True, "osOptions": OS_OPTIONS}


@router.post("/create")
async def create_session(req: CreateSessionRequest, db: DBSession = Depends(get_db)):
    session_id = str(uuid.uuid4())

    db_session = Session(
        id=session_id,
        os_type=req.osType or "alpine",
        snapshot_id=req.snapshotId,
        container_id=None,   # populated later when container is created
        tunnel_url=None,      # populated later when tunnel is created
    )
    db.add(db_session)

    db_participant = Participant(
        session_id=session_id,
        user_id=req.userId,
        username=req.username,
    )
    db.add(db_participant)

    db.commit()
    db.refresh(db_session)

    return {"success": True, "session": _session_to_dict(db_session)}


@router.get("/{session_id}")
async def get_session(session_id: str, db: DBSession = Depends(get_db)):
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True, "session": _session_to_dict(db_session)}


@router.post("/{session_id}/join")
async def join_session(session_id: str, participant: ParticipantCreate, db: DBSession = Depends(get_db)):
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    db_participant = Participant(
        session_id=session_id,
        user_id=participant.userId,
        username=participant.username,
    )
    db.add(db_participant)
    db.commit()
    db.refresh(db_session)

    return {"success": True, "session": _session_to_dict(db_session)}


@router.patch("/{session_id}")
async def update_session(session_id: str, container_id: str, db: DBSession = Depends(get_db)):
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    db_session.container_id = container_id
    db.commit()
    return {"success": True, "session": _session_to_dict(db_session)}


@router.delete("/{session_id}")
async def delete_session(session_id: str, db: DBSession = Depends(get_db)):
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(db_session)
    db.commit()
    return {"success": True, "message": f"Session {session_id} deleted"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _session_to_dict(s: Session) -> dict:
    return {
        "id": s.id,
        "osType": s.os_type,
        "containerId": s.container_id,
        "tunnelUrl": s.tunnel_url,
        "snapshotId": s.snapshot_id,
        "createdAt": s.created_at.isoformat() if s.created_at else None,
        "participants": [
            {
                "userId": p.user_id,
                "username": p.username,
                "joinedAt": p.joined_at.isoformat() if p.joined_at else None,
            }
            for p in s.participants
        ],
    }
