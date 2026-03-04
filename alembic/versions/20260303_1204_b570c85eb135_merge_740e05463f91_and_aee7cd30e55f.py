"""Merge 740e05463f91 and aee7cd30e55f

Revision ID: b570c85eb135
Revises: 740e05463f91, aee7cd30e55f
Create Date: 2026-03-03 12:04:37.159453

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b570c85eb135'
down_revision: Union[str, None] = 'e88b14b743a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema"""
    pass


def downgrade() -> None:
    """Downgrade database schema"""
    pass
