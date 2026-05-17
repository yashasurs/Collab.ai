from pydantic import BaseModel
from typing import List, Optional
import datetime


# ── Auth / User ─────────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: str
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str


# ── Participant ────────────────────────────────────────────────────────────────

class ParticipantBase(BaseModel):
    userId: str
    username: str


class ParticipantCreate(ParticipantBase):
    pass


class ParticipantOut(ParticipantBase):
    joinedAt: datetime.datetime

    class Config:
        from_attributes = True


# ── Session ────────────────────────────────────────────────────────────────────

class SessionOut(BaseModel):
    id: str
    createdAt: datetime.datetime
    participants: List[ParticipantOut]
    containerId: Optional[str] = None
    tunnelUrl: Optional[str] = None
    osType: str
    snapshotId: Optional[str] = None

    class Config:
        from_attributes = True


class CreateSessionRequest(BaseModel):
    osType: Optional[str] = "alpine"
    snapshotId: Optional[str] = None
    userId: str
    username: str


# ── Container ─────────────────────────────────────────────────────────────────

class CreateContainerRequest(BaseModel):
    osType: Optional[str] = "alpine"
    snapshotId: Optional[str] = None


class ExecCommandRequest(BaseModel):
    command: str


class SnapshotContainerRequest(BaseModel):
    name: str
    description: Optional[str] = None


# ── Tunnel ────────────────────────────────────────────────────────────────────

class CreateTunnelRequest(BaseModel):
    sessionId: str
    localPort: Optional[int] = 8080


# ── Snapshot ──────────────────────────────────────────────────────────────────

class SnapshotBase(BaseModel):
    name: str
    description: Optional[str] = None

class SnapshotCreate(SnapshotBase):
    sessionId: str

class SnapshotOut(SnapshotBase):
    id: str
    dockerImage: str
    createdAt: datetime.datetime

    class Config:
        from_attributes = True


# ── AI Agent ──────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str   # "user" | "assistant" | "system"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = "gemini-1.5-pro"


class ChatResponse(BaseModel):
    reply: str
    model: str