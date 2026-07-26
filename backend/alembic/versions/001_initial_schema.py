"""initial schema - users, sessions, participants, snapshots

Revision ID: 001_initial
Revises: None
Create Date: 2026-07-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('username', sa.String(), nullable=False, unique=True),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])

    # Sessions table
    op.create_table(
        'sessions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('os_type', sa.String(), nullable=False, server_default='alpine'),
        sa.Column('container_id', sa.String(), nullable=True),
        sa.Column('tunnel_url', sa.String(), nullable=True),
        sa.Column('snapshot_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_sessions_id', 'sessions', ['id'])

    # Participants table
    op.create_table(
        'participants',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('session_id', sa.String(), sa.ForeignKey('sessions.id'), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_participants_id', 'participants', ['id'])

    # Snapshots table
    op.create_table(
        'snapshots',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('docker_image', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_snapshots_id', 'snapshots', ['id'])


def downgrade() -> None:
    op.drop_table('participants')
    op.drop_table('snapshots')
    op.drop_table('sessions')
    op.drop_table('users')
