"""merge heads

Revision ID: eb76c1b5283e
Revises: 20241220_130000, 20250123_140000
Create Date: 2025-07-23 08:51:57.436814

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb76c1b5283e'
down_revision: Union[str, None] = ('20241220_130000', '20250123_140000')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
