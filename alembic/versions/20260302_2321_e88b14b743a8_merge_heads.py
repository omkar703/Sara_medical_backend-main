"""merge_heads

Revision ID: e88b14b743a8
Revises: 740e05463f91, aee7cd30e55f
Create Date: 2026-03-02 23:21:42.525841

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e88b14b743a8'
down_revision: Union[str, None] = ('740e05463f91', 'aee7cd30e55f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema"""
    pass


def downgrade() -> None:
    """Downgrade database schema"""
    pass
