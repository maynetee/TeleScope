"""merge heads

Revision ID: 3a400dd0fc64
Revises: 2b7f2dca2b5e, 9b1a1f0d7c2a
Create Date: 2026-01-16 23:32:58.895087

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a400dd0fc64'
down_revision: Union[str, None] = ('2b7f2dca2b5e', '9b1a1f0d7c2a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
