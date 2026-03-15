"""Production fix for missing database columns

Revision ID: a1b2c3d4e5f7
Revises: 0422ec1b753a
Create Date: 2026-03-15 21:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, None] = '0422ec1b753a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    
    # 1. Fix Users Table (is_active)
    user_columns = [col['name'] for col in inspector.get_columns('users')]
    if 'is_active' not in user_columns:
        op.add_column('users', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))
        print("✅ Added 'is_active' to 'users'")

    # 2. Fix Patients Table (home_phone, primary_doctor_id)
    patient_columns = [col['name'] for col in inspector.get_columns('patients')]
    if 'home_phone' not in patient_columns:
        op.add_column('patients', sa.Column('home_phone', sa.String(length=500), nullable=True))
        print("✅ Added 'home_phone' to 'patients'")
    
    if 'primary_doctor_id' not in patient_columns:
        op.add_column('patients', sa.Column('primary_doctor_id', sa.UUID(), nullable=True))
        op.create_foreign_key('fk_patients_primary_doctor', 'patients', 'users', ['primary_doctor_id'], ['id'])
        op.create_index(op.f('ix_patients_primary_doctor_id'), 'patients', ['primary_doctor_id'], unique=False)
        print("✅ Added 'primary_doctor_id' to 'patients'")

    # 3. Fix Invitations Table (staff_status, department_role)
    inv_columns = [col['name'] for col in inspector.get_columns('invitations')]
    if 'staff_status' not in inv_columns:
        op.add_column('invitations', sa.Column('staff_status', sa.String(length=20), server_default='Active', nullable=True))
        print("✅ Added 'staff_status' to 'invitations'")
    
    if 'department_role' not in inv_columns:
        op.add_column('invitations', sa.Column('department_role', sa.String(length=100), nullable=True))
        print("✅ Added 'department_role' to 'invitations'")


def downgrade() -> None:
    # We generally don't need detailed downgrades for production emergency fixes, 
    # but here is the basic structure.
    op.drop_column('invitations', 'department_role')
    op.drop_column('invitations', 'staff_status')
    op.drop_index(op.f('ix_patients_primary_doctor_id'), table_name='patients')
    op.drop_constraint('fk_patients_primary_doctor', 'patients', type_='foreignkey')
    op.drop_column('patients', 'primary_doctor_id')
    op.drop_column('patients', 'home_phone')
    op.drop_column('users', 'is_active')
