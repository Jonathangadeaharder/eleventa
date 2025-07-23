"""Add units table

Revision ID: 20250123_140000
Revises: 20241220_130000_add_product_unit_to_sale_items
Create Date: 2025-01-23 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20250123_140000'
down_revision = '20241220_120000'
branch_labels = None
depends_on = None


def upgrade():
    """Add units table for custom unit categories."""
    # Create units table
    op.create_table('units',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('abbreviation', sa.String(length=10), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_unit_name')
    )
    
    # Create index on name for faster lookups
    op.create_index('ix_units_name', 'units', ['name'])
    
    # Insert default units
    connection = op.get_bind()
    connection.execute(text("""
        INSERT INTO units (name, abbreviation, description, is_active) VALUES
        ('Unidad', 'Ud', 'Unidad individual', 1),
        ('Kilogramo', 'Kg', 'Unidad de peso', 1),
        ('Litro', 'L', 'Unidad de volumen', 1),
        ('Caja', 'Cj', 'Caja o paquete', 1),
        ('Metro', 'm', 'Unidad de longitud', 1),
        ('Docena', 'Dz', 'Conjunto de 12 unidades', 1)
    """))


def downgrade():
    """Remove units table."""
    # Drop index
    op.drop_index('ix_units_name', table_name='units')
    
    # Drop table
    op.drop_table('units')