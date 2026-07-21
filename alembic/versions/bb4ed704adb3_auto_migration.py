"""Auto migration

Revision ID: bb4ed704adb3
Revises: e7cf78a91706
Create Date: 2026-07-21 18:11:46.283668

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = 'bb4ed704adb3'
down_revision: Union[str, Sequence[str], None] = 'e7cf78a91706'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
