"""add_cash_drawer_entries_table

Revision ID: 1db174a25a49
Revises: 3bf9e6880467
Create Date: 2025-04-13 13:39:22.399083

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1db174a25a49'
down_revision: Union[str, None] = '3bf9e6880467'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the cash_drawer_entries table
    op.create_table('cash_drawer_entries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('entry_type', sa.String(), nullable=False),  # Will store enum as string
        sa.Column('amount', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('drawer_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for common queries
    op.create_index(op.f('ix_cash_drawer_entries_timestamp'), 'cash_drawer_entries', ['timestamp'], unique=False)
    op.create_index(op.f('ix_cash_drawer_entries_entry_type'), 'cash_drawer_entries', ['entry_type'], unique=False)
    op.create_index(op.f('ix_cash_drawer_entries_drawer_id'), 'cash_drawer_entries', ['drawer_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the indexes first
    op.drop_index(op.f('ix_cash_drawer_entries_drawer_id'), table_name='cash_drawer_entries')
    op.drop_index(op.f('ix_cash_drawer_entries_entry_type'), table_name='cash_drawer_entries')
    op.drop_index(op.f('ix_cash_drawer_entries_timestamp'), table_name='cash_drawer_entries')
    
    # Then drop the table
    op.drop_table('cash_drawer_entries')
