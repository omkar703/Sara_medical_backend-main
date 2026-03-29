"""repair_missing_columns_and_tables

Revision ID: f9b2c3d4e5f8
Revises: 70e05e24e9bb
Create Date: 2026-03-29 21:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f9b2c3d4e5f8'
down_revision: Union[str, None] = '70e05e24e9bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Ensure 'notifications' table exists (Safety)
    op.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id UUID PRIMARY KEY,
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
        type VARCHAR(50) NOT NULL,
        title VARCHAR(255) NOT NULL,
        message TEXT NOT NULL,
        is_read BOOLEAN DEFAULT FALSE,
        action_url TEXT,
        grant_id UUID,
        action_metadata JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    )
    """)
    
    # 2. Add missing columns to 'appointments'
    # We use 'IF NOT EXISTS' logic via raw SQL for maximum production safety
    columns_to_add = [
        ("scheduled_at", "TIMESTAMP WITH TIME ZONE"),
        ("hospital_id", "UUID REFERENCES organizations(id)"),
        ("reschedule_note", "TEXT"),
        ("approved_by_hospital", "UUID"),
        ("created_by", "VARCHAR(50) DEFAULT 'patient'"),
        ("google_event_id", "VARCHAR(255)"),
        ("meet_link", "TEXT")
    ]
    
    for col_name, col_type in columns_to_add:
        op.execute(f"ALTER TABLE appointments ADD COLUMN IF NOT EXISTS {col_name} {col_type}")

def downgrade() -> None:
    # Downgrade logic is optional for repair scripts but we'll at least drop the columns we added
    cols = ["scheduled_at", "hospital_id", "reschedule_note", "approved_by_hospital", "created_by", "google_event_id", "meet_link"]
    for col in cols:
        op.execute(f"ALTER TABLE appointments DROP COLUMN IF EXISTS {col}")
