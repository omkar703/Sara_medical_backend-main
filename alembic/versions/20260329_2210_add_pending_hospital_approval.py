"""add_pending_hospital_approval_to_enum

This migration adds 'pending_hospital_approval' to the appointment_status
PostgreSQL ENUM type. It chains after the repair migration.

Revision ID: cad819385621
Revises: f9b2c3d4e5f8
Create Date: 2026-03-29 22:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cad819385621'
down_revision = 'f9b2c3d4e5f8'  # Chains after the repair migration
branch_labels = None
depends_on = None


def upgrade():
    # Use raw connection to check if the enum value exists before adding it.
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block in Postgres,
    # so we issue a COMMIT first to end the implicit transaction.
    connection = op.get_bind()

    result = connection.execute(sa.text(
        "SELECT 1 FROM pg_enum "
        "WHERE enumlabel = 'pending_hospital_approval' "
        "AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'appointment_status')"
    )).fetchone()

    if not result:
        # End the current transaction so we can ALTER TYPE
        connection.execute(sa.text("COMMIT"))
        connection.execute(sa.text(
            "ALTER TYPE appointment_status ADD VALUE 'pending_hospital_approval'"
        ))


def downgrade():
    # Removing ENUM values in PostgreSQL is not straightforward.
    # A full type recreation would be required; skipping for safety.
    pass
