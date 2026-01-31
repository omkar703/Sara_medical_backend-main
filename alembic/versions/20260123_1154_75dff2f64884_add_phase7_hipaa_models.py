"""add_phase7_hipaa_models

Revision ID: 75dff2f64884
Revises: fe074cc8ef8e
Create Date: 2026-01-23 11:54:16.011655

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '75dff2f64884'
down_revision: Union[str, None] = 'fe074cc8ef8e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema: Add HIPAA models"""
    
    # Create AI Processing Queue table
    op.create_table('ai_processing_queue',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('patient_id', sa.UUID(), nullable=False),
        sa.Column('doctor_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('data_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('request_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', name='ai_queue_status'), nullable=False),
        sa.Column('result_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('queued_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_processing_queue_doctor_id'), 'ai_processing_queue', ['doctor_id'], unique=False)
    op.create_index(op.f('ix_ai_processing_queue_organization_id'), 'ai_processing_queue', ['organization_id'], unique=False)
    op.create_index(op.f('ix_ai_processing_queue_patient_id'), 'ai_processing_queue', ['patient_id'], unique=False)
    op.create_index(op.f('ix_ai_processing_queue_status'), 'ai_processing_queue', ['status'], unique=False)

    # Create Data Access Grants table
    op.create_table('data_access_grants',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('patient_id', sa.UUID(), nullable=False),
        sa.Column('doctor_id', sa.UUID(), nullable=False),
        sa.Column('appointment_id', sa.UUID(), nullable=True),
        sa.Column('grant_reason', sa.String(length=255), nullable=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id']),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_access_grants_doctor_id'), 'data_access_grants', ['doctor_id'], unique=False)
    op.create_index(op.f('ix_data_access_grants_patient_id'), 'data_access_grants', ['patient_id'], unique=False)


def downgrade() -> None:
    """Downgrade database schema"""
    op.drop_index(op.f('ix_data_access_grants_patient_id'), table_name='data_access_grants')
    op.drop_index(op.f('ix_data_access_grants_doctor_id'), table_name='data_access_grants')
    op.drop_table('data_access_grants')
    op.drop_index(op.f('ix_ai_processing_queue_status'), table_name='ai_processing_queue')
    op.drop_index(op.f('ix_ai_processing_queue_patient_id'), table_name='ai_processing_queue')
    op.drop_index(op.f('ix_ai_processing_queue_organization_id'), table_name='ai_processing_queue')
    op.drop_index(op.f('ix_ai_processing_queue_doctor_id'), table_name='ai_processing_queue')
    op.drop_table('ai_processing_queue')
    op.execute("DROP TYPE ai_queue_status")
