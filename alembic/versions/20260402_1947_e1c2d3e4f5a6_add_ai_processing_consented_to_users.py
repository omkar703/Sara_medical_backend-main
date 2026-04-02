"""add_ai_processing_consented_to_users

Revision ID: e1c2d3e4f5a6
Revises: cad819385621
Create Date: 2026-04-02 19:47:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1c2d3e4f5a6'
down_revision = 'cad819385621'
branch_labels = None
depends_on = None


def upgrade():
    # Adding the ai_processing_consented column to the users table
    # We use IF NOT EXISTS logic via raw SQL for maximum production safety
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_processing_consented BOOLEAN DEFAULT FALSE NOT NULL")


def downgrade():
    # Removing the ai_processing_consented column from the users table
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS ai_processing_consented")
