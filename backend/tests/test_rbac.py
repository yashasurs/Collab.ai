"""Tests for RBAC logic and models."""

import pytest
import uuid

from app.models.rbac import Role, Permission, Organization, UserOrganization
from app.auth.rbac import RBACService, ROLE_VIEWER, ROLE_MEMBER, ROLE_ADMIN, ROLE_OWNER


@pytest.fixture
def setup_rbac_data(db_session):
    """Seed test database with roles and permissions."""
    # Create roles
    r_viewer = Role(id="role_viewer", name=ROLE_VIEWER, level=10)
    r_member = Role(id="role_member", name=ROLE_MEMBER, level=20)
    
    # Create permissions
    p_read = Permission(id="perm_session_read", resource="session", action="read")
    p_create = Permission(id="perm_session_create", resource="session", action="create")
    
    # Assign permissions
    r_viewer.permissions.append(p_read)
    r_member.permissions.append(p_read)
    r_member.permissions.append(p_create)
    
    db_session.add_all([r_viewer, r_member, p_read, p_create])
    db_session.commit()
    
    return {"r_viewer": r_viewer, "r_member": r_member, "p_read": p_read, "p_create": p_create}


class TestRBACService:
    """Test RBACService logic."""

    def test_has_permission(self, db_session, setup_rbac_data):
        rbac = RBACService(db_session)
        
        # Viewer should have read but not create
        assert rbac.has_permission(setup_rbac_data["r_viewer"], "session", "read") is True
        assert rbac.has_permission(setup_rbac_data["r_viewer"], "session", "create") is False
        
        # Member should have both
        assert rbac.has_permission(setup_rbac_data["r_member"], "session", "read") is True
        assert rbac.has_permission(setup_rbac_data["r_member"], "session", "create") is True
        
        # Non-existent permission
        assert rbac.has_permission(setup_rbac_data["r_member"], "ghost", "boo") is False

    def test_check_role_level(self, db_session, setup_rbac_data):
        rbac = RBACService(db_session)
        r_viewer = setup_rbac_data["r_viewer"]
        r_member = setup_rbac_data["r_member"]
        
        # Viewer is level 10
        assert rbac.check_role_level(r_viewer, ROLE_VIEWER) is True
        assert rbac.check_role_level(r_viewer, ROLE_MEMBER) is False
        
        # Member is level 20
        assert rbac.check_role_level(r_member, ROLE_VIEWER) is True
        assert rbac.check_role_level(r_member, ROLE_MEMBER) is True
        assert rbac.check_role_level(r_member, ROLE_ADMIN) is False

    def test_get_user_org_role(self, db_session, test_user, setup_rbac_data):
        # Create org
        org = Organization(id=str(uuid.uuid4()), name="Test Org", slug="test-org")
        db_session.add(org)
        
        # Add user to org as member
        membership = UserOrganization(
            user_id=test_user.id,
            organization_id=org.id,
            role_id=setup_rbac_data["r_member"].id
        )
        db_session.add(membership)
        db_session.commit()
        
        rbac = RBACService(db_session)
        role = rbac.get_user_org_role(test_user.id, org.id)
        
        assert role is not None
        assert role.name == ROLE_MEMBER
        assert role.level == 20
