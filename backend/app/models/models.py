from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True)
    os_type = Column(String, nullable=False, default="alpine")
    container_id = Column(String, nullable=True)
    tunnel_url = Column(String, nullable=True)
    snapshot_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    participants = relationship("Participant", back_populates="session", cascade="all, delete-orphan")


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    user_id = Column(String, nullable=False)
    username = Column(String, nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="participants")


class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    docker_image = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())