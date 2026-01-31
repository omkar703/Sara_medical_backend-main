"""create_tasks_table

Revision ID: a4b6883a1f45
Revises: f0dc6048fe0b
Create Date: 2026-01-23 07:47:42.136099

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4b6883a1f45'
down_revision: Union[str, None] = 'f0dc6048fe0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema"""
    
    op.create_table('tasks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('doctor_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('priority', sa.Enum('urgent', 'normal', name='task_priority'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'completed', name='task_status'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_doctor_id'), 'tasks', ['doctor_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema"""
    op.drop_index(op.f('ix_tasks_doctor_id'), table_name='tasks')
    op.drop_table('tasks')
    op.execute("DROP TYPE task_status")
    op.execute("DROP TYPE task_priority")
