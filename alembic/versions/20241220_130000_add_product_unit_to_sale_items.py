"""Add product_unit to sale_items

Revision ID: 20241220_130000
Revises: 20241220_120000
Create Date: 2024-12-20 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20241220_130000'
down_revision = '20241220_120000'
branch_labels = None
depends_on = None


def upgrade():
    # Add product_unit column to sale_items table
    op.add_column('sale_items', sa.Column('product_unit', sa.String(), nullable=True, default='Unidad'))
    
    # Update existing records to have default unit
    op.execute("UPDATE sale_items SET product_unit = 'Unidad' WHERE product_unit IS NULL")


def downgrade():
    # Remove product_unit column from sale_items table
    op.drop_column('sale_items', 'product_unit')