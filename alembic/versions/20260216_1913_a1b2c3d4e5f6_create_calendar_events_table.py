"""create_calendar_events_table

Revision ID: a1b2c3d4e5f6
Revises: 7e27fda403a5
Create Date: 2026-02-16 19:13:33.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '7e27fda403a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop the table if it was left behind
    op.execute("DROP TABLE IF EXISTS calendar_events CASCADE;")
    
    # 2. Drop the types (you already have these from the last step)
    op.execute("DROP TYPE IF EXISTS calendar_event_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS calendar_event_status CASCADE;")
    
    # 3. Create the table
    op.create_table(
        'calendar_events',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        
        # Event Details
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('all_day', sa.Boolean(), default=False, nullable=False),
        
        # Event Type & Linked Resources
        sa.Column('event_type', sa.Enum('appointment', 'custom', 'task', name='calendar_event_type'), nullable=False),
        sa.Column('appointment_id', sa.UUID(), nullable=True),
        sa.Column('task_id', sa.UUID(), nullable=True),
        
        # Customization
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('reminder_minutes', sa.Integer(), nullable=True),
        
        # Status
        sa.Column('status', sa.Enum('scheduled', 'completed', 'cancelled', name='calendar_event_status'), 
                  default='scheduled', nullable=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        # Foreign Keys
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_calendar_events_user_id', 'calendar_events', ['user_id'])
    op.create_index('idx_calendar_events_org_id', 'calendar_events', ['organization_id'])
    op.create_index('idx_calendar_events_start_time', 'calendar_events', ['start_time'])
    op.create_index('idx_calendar_events_event_type', 'calendar_events', ['event_type'])
    op.create_index('idx_calendar_events_user_daterange', 'calendar_events', ['user_id', 'start_time', 'end_time'])


def downgrade() -> None:
    """Downgrade database schema - Drop calendar_events table"""
    
    # Drop indexes
    op.drop_index('idx_calendar_events_user_daterange', table_name='calendar_events')
    op.drop_index('idx_calendar_events_event_type', table_name='calendar_events')
    op.drop_index('idx_calendar_events_start_time', table_name='calendar_events')
    op.drop_index('idx_calendar_events_org_id', table_name='calendar_events')
    op.drop_index('idx_calendar_events_user_id', table_name='calendar_events')
    
    # Drop table
    op.drop_table('calendar_events')
    
    # Drop ENUM types
    op.execute("DROP TYPE calendar_event_status")
    op.execute("DROP TYPE calendar_event_type")
