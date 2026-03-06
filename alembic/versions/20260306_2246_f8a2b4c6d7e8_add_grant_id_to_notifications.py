"""add grant_id and action_metadata to notifications

Revision ID: f8a2b4c6d7e8
Revises: 2c8b6c6a9d3d
Create Date: 2026-03-06 22:46:00.000000

Adds two columns to the `notifications` table:
  * grant_id        – nullable FK → data_access_grants.id (SET NULL on delete)
  * action_metadata – nullable JSONB for approve/reject button context
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = 'f8a2b4c6d7e8'
down_revision: Union[str, None] = 'add_chat_sessions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add grant_id and action_metadata to notifications table."""
    from sqlalchemy.engine.reflection import Inspector
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    existing_cols = [col['name'] for col in inspector.get_columns('notifications')]

    if 'grant_id' not in existing_cols:
        op.add_column(
            'notifications',
            sa.Column(
                'grant_id',
                PG_UUID(as_uuid=True),
                sa.ForeignKey('data_access_grants.id', ondelete='SET NULL'),
                nullable=True
            )
        )
        op.create_index(
            'ix_notifications_grant_id',
            'notifications',
            ['grant_id'],
            unique=False
        )

    if 'action_metadata' not in existing_cols:
        op.add_column(
            'notifications',
            sa.Column('action_metadata', JSONB, nullable=True)
        )


def downgrade() -> None:
    """Remove grant_id and action_metadata from notifications table."""
    op.drop_index('ix_notifications_grant_id', table_name='notifications')
    op.drop_column('notifications', 'action_metadata')
    op.drop_column('notifications', 'grant_id')
