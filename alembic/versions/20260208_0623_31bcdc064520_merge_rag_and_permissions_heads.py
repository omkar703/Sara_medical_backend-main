"""merge_rag_and_permissions_heads

Revision ID: 31bcdc064520
Revises: 893b46ddf1d9, dec5e5a04348
Create Date: 2026-02-08 06:23:16.972801

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '31bcdc064520'
down_revision: Union[str, None] = ('893b46ddf1d9', 'dec5e5a04348')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema"""
    pass


def downgrade() -> None:
    """Downgrade database schema"""
    pass
