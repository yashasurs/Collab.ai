"""add RBAC tables - organizations, teams, roles, permissions

Revision ID: 002_add_rbac
Revises: 001_initial
Create Date: 2026-07-26
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_rbac'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False, unique=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('level', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_index('ix_roles_id', 'roles', ['id'])

    # Permissions table
    op.create_table(
        'permissions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('resource', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
    )
    op.create_index('ix_permissions_id', 'permissions', ['id'])

    # Role-Permission association
    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.String(), sa.ForeignKey('roles.id'), primary_key=True),
        sa.Column('permission_id', sa.String(), sa.ForeignKey('permissions.id'), primary_key=True),
    )

    # Organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_organizations_id', 'organizations', ['id'])
    op.create_index('ix_organizations_slug', 'organizations', ['slug'])

    # Teams table
    op.create_table(
        'teams',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('organization_id', sa.String(), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_teams_id', 'teams', ['id'])

    # User-Organization membership
    op.create_table(
        'user_organizations',
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('organization_id', sa.String(), sa.ForeignKey('organizations.id'), primary_key=True),
        sa.Column('role_id', sa.String(), sa.ForeignKey('roles.id'), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # User-Team membership
    op.create_table(
        'user_teams',
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('team_id', sa.String(), sa.ForeignKey('teams.id'), primary_key=True),
        sa.Column('role_id', sa.String(), sa.ForeignKey('roles.id'), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Seed default roles and permissions ─────────────────────────────────
    roles_table = sa.table(
        'roles',
        sa.column('id', sa.String),
        sa.column('name', sa.String),
        sa.column('description', sa.String),
        sa.column('level', sa.Integer),
    )
    permissions_table = sa.table(
        'permissions',
        sa.column('id', sa.String),
        sa.column('resource', sa.String),
        sa.column('action', sa.String),
    )
    role_perms_table = sa.table(
        'role_permissions',
        sa.column('role_id', sa.String),
        sa.column('permission_id', sa.String),
    )

    # Seed roles
    roles = [
        {"id": "role_viewer",  "name": "viewer",  "description": "Read-only access",           "level": 10},
        {"id": "role_member",  "name": "member",  "description": "Can create and edit",         "level": 20},
        {"id": "role_admin",   "name": "admin",   "description": "Full management access",      "level": 30},
        {"id": "role_owner",   "name": "owner",   "description": "Organization owner",          "level": 40},
    ]
    op.bulk_insert(roles_table, roles)

    # Seed permissions
    resources = ["session", "container", "snapshot", "tunnel", "org", "team"]
    actions = ["create", "read", "update", "delete"]
    perms = []
    for resource in resources:
        for action in actions:
            perms.append({
                "id": f"perm_{resource}_{action}",
                "resource": resource,
                "action": action,
            })
    op.bulk_insert(permissions_table, perms)

    # Assign permissions to roles
    role_perm_assignments = []
    for resource in resources:
        # Viewer: read only
        role_perm_assignments.append({"role_id": "role_viewer", "permission_id": f"perm_{resource}_read"})
        # Member: read + create + update
        for action in ["create", "read", "update"]:
            role_perm_assignments.append({"role_id": "role_member", "permission_id": f"perm_{resource}_{action}"})
        # Admin & Owner: all actions
        for action in actions:
            role_perm_assignments.append({"role_id": "role_admin", "permission_id": f"perm_{resource}_{action}"})
            role_perm_assignments.append({"role_id": "role_owner", "permission_id": f"perm_{resource}_{action}"})

    op.bulk_insert(role_perms_table, role_perm_assignments)


def downgrade() -> None:
    op.drop_table('user_teams')
    op.drop_table('user_organizations')
    op.drop_table('role_permissions')
    op.drop_table('teams')
    op.drop_table('organizations')
    op.drop_table('permissions')
    op.drop_table('roles')
