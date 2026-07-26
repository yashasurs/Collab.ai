"""
RBAC (Role-Based Access Control) models.

Implements a 4-level permission hierarchy:
  Organization → Team → Role → Permission

This allows fine-grained access control for multi-tenant collaboration.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


# ---------------------------------------------------------------------------
# Association tables
# ---------------------------------------------------------------------------

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", String, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", String, ForeignKey("permissions.id"), primary_key=True),
)


# ---------------------------------------------------------------------------
# Organization
# ---------------------------------------------------------------------------

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    teams = relationship("Team", back_populates="organization", cascade="all, delete-orphan")
    members = relationship("UserOrganization", back_populates="organization", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Team (belongs to an Organization)
# ---------------------------------------------------------------------------

class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True, index=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="teams")
    members = relationship("UserTeam", back_populates="team", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Role (admin, member, viewer)
# ---------------------------------------------------------------------------

class Role(Base):
    __tablename__ = "roles"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # "admin", "member", "viewer"
    description = Column(String, nullable=True)
    level = Column(Integer, nullable=False, default=0)  # Higher = more privilege

    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")


# ---------------------------------------------------------------------------
# Permission (resource + action)
# ---------------------------------------------------------------------------

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(String, primary_key=True, index=True)
    resource = Column(String, nullable=False)  # "session", "container", "snapshot", "tunnel", "org", "team"
    action = Column(String, nullable=False)     # "create", "read", "update", "delete"

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


# ---------------------------------------------------------------------------
# User ↔ Organization membership
# ---------------------------------------------------------------------------

class UserOrganization(Base):
    __tablename__ = "user_organizations"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    organization_id = Column(String, ForeignKey("organizations.id"), primary_key=True)
    role_id = Column(String, ForeignKey("roles.id"), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="members")
    role = relationship("Role")


# ---------------------------------------------------------------------------
# User ↔ Team membership
# ---------------------------------------------------------------------------

class UserTeam(Base):
    __tablename__ = "user_teams"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    team_id = Column(String, ForeignKey("teams.id"), primary_key=True)
    role_id = Column(String, ForeignKey("roles.id"), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    team = relationship("Team", back_populates="members")
    role = relationship("Role")
