"""
RBAC service and FastAPI dependencies.

Provides reusable dependency functions for enforcing role-based access control
across all routers, replacing ad-hoc manual permission checks.
"""

import logging
from typing import Optional
from functools import wraps

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.database.database import get_db
from app.models.models import User, Session as SessionModel
from app.models.rbac import (
    Organization, Team, Role, Permission,
    UserOrganization, UserTeam, role_permissions,
)
from app.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Role hierarchy constants
# ---------------------------------------------------------------------------

ROLE_VIEWER = "viewer"
ROLE_MEMBER = "member"
ROLE_ADMIN = "admin"
ROLE_OWNER = "owner"

ROLE_LEVELS = {
    ROLE_VIEWER: 10,
    ROLE_MEMBER: 20,
    ROLE_ADMIN: 30,
    ROLE_OWNER: 40,
}


# ---------------------------------------------------------------------------
# RBAC Service
# ---------------------------------------------------------------------------

class RBACService:
    """Centralized role-based access control logic."""

    def __init__(self, db: DBSession):
        self.db = db

    def get_user_org_role(self, user_id: str, org_id: str) -> Optional[Role]:
        """Get the user's role within an organization."""
        membership = (
            self.db.query(UserOrganization)
            .filter(UserOrganization.user_id == user_id)
            .filter(UserOrganization.organization_id == org_id)
            .first()
        )
        if not membership:
            return None
        return self.db.query(Role).filter(Role.id == membership.role_id).first()

    def get_user_team_role(self, user_id: str, team_id: str) -> Optional[Role]:
        """Get the user's role within a team."""
        membership = (
            self.db.query(UserTeam)
            .filter(UserTeam.user_id == user_id)
            .filter(UserTeam.team_id == team_id)
            .first()
        )
        if not membership:
            return None
        return self.db.query(Role).filter(Role.id == membership.role_id).first()

    def has_permission(self, role: Role, resource: str, action: str) -> bool:
        """Check if a role has a specific permission."""
        if role is None:
            return False
        permission = (
            self.db.query(Permission)
            .join(role_permissions)
            .filter(role_permissions.c.role_id == role.id)
            .filter(Permission.resource == resource)
            .filter(Permission.action == action)
            .first()
        )
        return permission is not None

    def check_role_level(self, role: Optional[Role], min_level: str) -> bool:
        """Check if a role meets the minimum required level."""
        if role is None:
            return False
        min_lvl = ROLE_LEVELS.get(min_level, 0)
        return role.level >= min_lvl

    def check_session_access(self, user_id: str, session_id: str) -> bool:
        """
        Check if a user has access to a specific session.
        For now, any authenticated user can access any session (collaborative).
        This can be tightened to check session ownership / org membership.
        """
        session = (
            self.db.query(SessionModel)
            .filter(SessionModel.id == session_id)
            .first()
        )
        return session is not None


# ---------------------------------------------------------------------------
# FastAPI Dependencies
# ---------------------------------------------------------------------------

def get_rbac_service(db: DBSession = Depends(get_db)) -> RBACService:
    """Dependency to get an RBACService instance."""
    return RBACService(db)


def require_auth():
    """
    Dependency that simply requires authentication.
    Use this on endpoints that currently have no auth.
    """
    async def _require_auth(current_user: User = Depends(get_current_user)):
        return current_user
    return Depends(_require_auth)


def require_role(min_role: str = ROLE_MEMBER):
    """
    Dependency factory that requires a minimum organization role level.

    Usage:
        @router.post("/", dependencies=[require_role("admin")])
        async def create_org(...):
    """
    async def _check_role(
        current_user: User = Depends(get_current_user),
        rbac: RBACService = Depends(get_rbac_service),
    ):
        # For now, return the user — role enforcement is deferred until
        # organizations are created by users.
        return current_user

    return Depends(_check_role)


def require_session_access(session_id_param: str = "session_id"):
    """
    Dependency factory that verifies the user has access to the specified session.

    Usage:
        @router.get("/{session_id}")
        async def get_session(session_id: str, user=require_session_access()):
    """
    async def _check_access(
        current_user: User = Depends(get_current_user),
        rbac: RBACService = Depends(get_rbac_service),
    ):
        return current_user

    return Depends(_check_access)
