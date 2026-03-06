"""add chat_sessions and chat_messages tables

Revision ID: add_chat_sessions
Revises: b570c85eb135
Create Date: 2026-03-05 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = 'add_chat_sessions'
down_revision = 'b570c85eb135'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Check for existing tables ---
    from sqlalchemy.engine.reflection import Inspector
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    tables = inspector.get_table_names()

    # ── chat_sessions ──────────────────────────────────────────────────────────
    if 'chat_sessions' not in tables:
        op.create_table(
            'chat_sessions',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('doctor_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('patient_id', UUID(as_uuid=True), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('title', sa.String(255), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        )
        op.create_index('ix_chat_sessions_doctor_patient', 'chat_sessions', ['doctor_id', 'patient_id'])

    # ── chat_messages ──────────────────────────────────────────────────────────
    if 'chat_messages' not in tables:
        op.create_table(
            'chat_messages',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('role', sa.String(20), nullable=False),
            sa.Column('content', sa.Text, nullable=False),
            sa.Column('sources', JSONB, nullable=True),
            sa.Column('confidence', sa.String(20), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        )


def downgrade() -> None:
    op.drop_table('chat_messages')
    op.drop_index('ix_chat_sessions_doctor_patient', table_name='chat_sessions')
    op.drop_table('chat_sessions')
