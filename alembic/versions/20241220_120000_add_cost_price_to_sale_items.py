"""Add cost_price to sale_items

Revision ID: 20241220_120000
Revises: 
Create Date: 2024-12-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20241220_120000'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create departments table
    op.create_table('departments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create products table
    op.create_table('products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('cost_price', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('sell_price', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('wholesale_price', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('special_price', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('barcode', sa.String(length=50), nullable=True),
        sa.Column('brand', sa.String(length=50), nullable=True),
        sa.Column('model', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('quantity_in_stock', sa.Numeric(precision=15, scale=3), nullable=True),
        sa.Column('min_stock', sa.Numeric(precision=15, scale=3), nullable=True),
        sa.Column('max_stock', sa.Numeric(precision=15, scale=3), nullable=True),
        sa.Column('uses_inventory', sa.Boolean(), nullable=True),
        sa.Column('is_service', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create sales table
    op.create_table('sales',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=True), # Assuming customer table might exist or be added later
        sa.Column('is_credit_sale', sa.Boolean(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True), # Assuming user table might exist or be added later
        sa.Column('payment_type', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create sale_items table (including the cost_price column as originally intended for this file)
    op.create_table('sale_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sale_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=3), nullable=False), # Adjusted precision based on Product model
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('product_code', sa.String(length=50), nullable=True),
        sa.Column('product_description', sa.String(length=255), nullable=True),
        sa.Column('cost_price', sa.Numeric(precision=10, scale=2), nullable=False, server_default=sa.text("'0.00'")),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['sale_id'], ['sales.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create invoices table
    op.create_table('invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sale_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('invoice_number', sa.String(), nullable=True),
        sa.Column('invoice_date', sa.DateTime(), nullable=False),
        sa.Column('invoice_type', sa.String(length=1), nullable=False, server_default='B'), # Default based on model
        sa.Column('customer_details', sa.JSON(), nullable=True), # Using JSON for Dict
        sa.Column('subtotal', sa.Numeric(precision=10, scale=2), nullable=False, server_default=sa.text("'0.00'")),
        sa.Column('iva_amount', sa.Numeric(precision=10, scale=2), nullable=False, server_default=sa.text("'0.00'")),
        sa.Column('total', sa.Numeric(precision=10, scale=2), nullable=False, server_default=sa.text("'0.00'")),
        sa.Column('iva_condition', sa.String(), nullable=True, server_default='Consumidor Final'), # Default based on model
        sa.Column('cae', sa.String(), nullable=True),
        sa.Column('cae_due_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()), # Default based on model
        sa.ForeignKeyConstraint(['sale_id'], ['sales.id'], ),
        # Assuming customer_id might eventually link to a customers table
        # sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ), 
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('invoices')
    op.drop_table('sale_items')
    op.drop_table('sales')
    op.drop_table('products')
    op.drop_table('departments')