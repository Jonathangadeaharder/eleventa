import unittest
import pytest
from decimal import Decimal
from datetime import datetime
import uuid
from typing import Optional

# Import domain models
from core.models.sale import Sale, SaleItem
from core.models.product import Product, Department
from core.interfaces.repository_interfaces import ISaleRepository

# Import application ORM models
from infrastructure.persistence.sqlite.models_mapping import (
    DepartmentOrm, ProductOrm, SaleOrm, SaleItemOrm, UserOrm, CustomerOrm # Add UserOrm, CustomerOrm if needed
)

# Test-specific repository implementation
class _HelperSqliteSaleRepository(ISaleRepository):
    """SQLite implementation of Sale Repository for testing."""
    
    def __init__(self, session):
        self._session = session
    
    def add_sale(self, sale: Sale) -> Sale:
        """Add a new sale to the repository."""
        try:
            # Create new SaleOrm object without constructor params
            sale_orm = SaleOrm()
            sale_orm.date_time = sale.timestamp
            sale_orm.total_amount = float(sale.total)
            sale_orm.payment_type = sale.payment_type
            sale_orm.customer_id = sale.customer_id
            sale_orm.user_id = sale.user_id
            
            # Add sale to session to generate ID
            self._session.add(sale_orm)
            self._session.flush()
            
            # Update the sale with generated ID
            sale.id = sale_orm.id
            
            # Create and add each sale item
            for item in sale.items:
                item_orm = SaleItemOrm()
                item_orm.sale_id = sale_orm.id
                item_orm.product_id = item.product_id
                item_orm.quantity = float(item.quantity)
                item_orm.unit_price = float(item.unit_price)
                item_orm.total_price = float(item.quantity * item.unit_price)
                item_orm.product_code = item.product_code
                item_orm.product_description = item.product_description
                
                self._session.add(item_orm)
                self._session.flush()
                
                # Update the item with generated ID
                item.id = item_orm.id
                item.sale_id = sale_orm.id
            
            return sale
        except Exception as e:
            self._session.rollback()
            raise ValueError(f"Error adding sale: {e}")
    
    def get_sales_by_period(self, start_time: datetime, end_time: datetime) -> list:
        """Get all sales within the specified period."""
        try:
            query = self._session.query(SaleOrm).filter(
                SaleOrm.date_time >= start_time,
                SaleOrm.date_time <= end_time
            ).order_by(SaleOrm.date_time)
            
            sales = []
            for sale_orm in query.all():
                # Get associated items
                items_query = self._session.query(SaleItemOrm).filter(
                    SaleItemOrm.sale_id == sale_orm.id
                )
                item_orms = items_query.all()
                
                # Map to domain models
                sale_items = [self._map_sale_item_orm_to_model(item) for item in item_orms]
                sale = self._map_sale_orm_to_model(sale_orm, sale_items)
                sales.append(sale)
            
            return sales
        except Exception as e:
            return []
    
    def get_sale_by_id(self, sale_id: int):
        """Get a sale by its ID."""
        try:
            sale_orm = self._session.query(SaleOrm).filter(SaleOrm.id == sale_id).first()
            if not sale_orm:
                return None
                
            # Get associated items
            items_orm = self._session.query(SaleItemOrm).filter(SaleItemOrm.sale_id == sale_id).all()
            
            # Map to domain models
            sale_items = [self._map_sale_item_orm_to_model(item) for item in items_orm]
            
            # Map the sale
            return self._map_sale_orm_to_model(sale_orm, sale_items)
        except Exception as e:
            return None
    
    def get_by_id(self, sale_id: int) -> Optional[Sale]:
        """Get a single sale by its ID, including its items."""
        try:
            sale_orm = self._session.query(SaleOrm).filter(SaleOrm.id == sale_id).first()
            if not sale_orm:
                return None

            # Get associated items eagerly (adjust if lazy loading is default and preferred)
            items_orm = self._session.query(SaleItemOrm).filter(SaleItemOrm.sale_id == sale_id).all()
            sale_items = [self._map_sale_item_orm_to_model(item) for item in items_orm]

            return self._map_sale_orm_to_model(sale_orm, sale_items)
        except Exception as e:
            # Log the error appropriately
            # logger.error(f"Error retrieving sale with ID {sale_id}: {e}")
            return None
    
    def _map_sale_item_orm_to_model(self, item_orm):
        """Map a SaleItemOrm to a SaleItem model."""
        return SaleItem(
            id=item_orm.id,
            sale_id=item_orm.sale_id,
            product_id=item_orm.product_id,
            quantity=Decimal(str(item_orm.quantity)),
            unit_price=Decimal(str(item_orm.unit_price)),
            product_code=item_orm.product_code,
            product_description=item_orm.product_description
        )
    
    def _map_sale_orm_to_model(self, sale_orm, sale_items=None):
        """Map a SaleOrm to a Sale model."""
        return Sale(
            id=sale_orm.id,
            timestamp=sale_orm.date_time,
            items=sale_items or [],
            payment_type=sale_orm.payment_type,
            customer_id=sale_orm.customer_id,
            user_id=sale_orm.user_id
        )
    
    # Implementation of required methods for our tests
    def get_sales_summary_by_period(self, start_date=None, end_date=None, group_by="day"):
        """Get sales summary by period, grouped by day, week, or month."""
        from sqlalchemy import func, extract
        
        # Convert dates to datetime if needed
        if start_date and not isinstance(start_date, datetime):
            start_date = datetime.combine(start_date, datetime.min.time())
        if end_date and not isinstance(end_date, datetime):
            end_date = datetime.combine(end_date, datetime.max.time())
        
        # Base query
        query = self._session.query(
            SaleOrm.date_time.label('date'),
            func.count(SaleOrm.id).label('num_sales'),
            func.sum(SaleOrm.total_amount).label('total_sales')
        )
        
        # Apply date filters
        if start_date:
            query = query.filter(SaleOrm.date_time >= start_date)
        if end_date:
            query = query.filter(SaleOrm.date_time <= end_date)
        
        # Group by selected period
        if group_by == 'day':
            query = query.group_by(
                extract('year', SaleOrm.date_time),
                extract('month', SaleOrm.date_time),
                extract('day', SaleOrm.date_time)
            )
        elif group_by == 'week':
            query = query.group_by(
                extract('year', SaleOrm.date_time),
                extract('week', SaleOrm.date_time)
            )
        elif group_by == 'month':
            query = query.group_by(
                extract('year', SaleOrm.date_time),
                extract('month', SaleOrm.date_time)
            )
        
        # Order by date
        query = query.order_by(SaleOrm.date_time)
        
        # Execute and format results
        result = []
        for row in query.all():
            result.append({
                'date': row.date.date(),
                'num_sales': row.num_sales,
                'total_sales': row.total_sales or 0
            })
        
        return result
    
    def get_sales_by_payment_type(self, start_date=None, end_date=None):
        """Get sales aggregated by payment type."""
        from sqlalchemy import func
        
        # Convert dates to datetime if needed
        if start_date and not isinstance(start_date, datetime):
            start_date = datetime.combine(start_date, datetime.min.time())
        if end_date and not isinstance(end_date, datetime):
            end_date = datetime.combine(end_date, datetime.max.time())
        
        # Base query
        query = self._session.query(
            SaleOrm.payment_type.label('payment_type'),
            func.count(SaleOrm.id).label('num_sales'),
            func.sum(SaleOrm.total_amount).label('total_sales')
        )
        
        # Apply date filters
        if start_date:
            query = query.filter(SaleOrm.date_time >= start_date)
        if end_date:
            query = query.filter(SaleOrm.date_time <= end_date)
        
        # Group by payment type
        query = query.group_by(SaleOrm.payment_type)
        
        # Execute and format results
        result = []
        for row in query.all():
            result.append({
                'payment_type': row.payment_type or 'Unknown',
                'num_sales': row.num_sales,
                'total_sales': row.total_sales or 0
            })
        
        return result
    
    def get_sales_by_department(self, start_date=None, end_date=None):
        """Get sales aggregated by department."""
        from sqlalchemy import func
        
        # Convert dates to datetime if needed
        if start_date and not isinstance(start_date, datetime):
            start_date = datetime.combine(start_date, datetime.min.time())
        if end_date and not isinstance(end_date, datetime):
            end_date = datetime.combine(end_date, datetime.max.time())
        
        # Join query to get department info
        query = self._session.query(
            DepartmentOrm.name.label('department_name'),
            func.count(SaleOrm.id.distinct()).label('num_sales'),
            func.sum(SaleItemOrm.quantity * SaleItemOrm.unit_price).label('total_sales')
        ).join(
            SaleItemOrm, SaleItemOrm.sale_id == SaleOrm.id
        ).join(
            ProductOrm, ProductOrm.id == SaleItemOrm.product_id
        ).join(
            DepartmentOrm, DepartmentOrm.id == ProductOrm.department_id
        )
        
        # Apply date filters
        if start_date:
            query = query.filter(SaleOrm.date_time >= start_date)
        if end_date:
            query = query.filter(SaleOrm.date_time <= end_date)
        
        # Group by department
        query = query.group_by(DepartmentOrm.name)
        
        # Execute and format results
        result = []
        for row in query.all():
            result.append({
                'department_name': row.department_name,
                'num_sales': row.num_sales,
                'total_sales': row.total_sales or 0
            })
        
        return result
    
    def get_sales_by_customer(self, start_date=None, end_date=None, limit=10):
        """Get sales aggregated by customer."""
        from sqlalchemy import func
        
        # Convert dates to datetime if needed
        if start_date and not isinstance(start_date, datetime):
            start_date = datetime.combine(start_date, datetime.min.time())
        if end_date and not isinstance(end_date, datetime):
            end_date = datetime.combine(end_date, datetime.max.time())
        
        # Base query
        query = self._session.query(
            SaleOrm.customer_id.label('customer_id'),
            func.count(SaleOrm.id).label('num_sales'),
            func.sum(SaleOrm.total_amount).label('total_sales')
        )
        
        # Filter out null customer_id
        query = query.filter(SaleOrm.customer_id.isnot(None))
        
        # Apply date filters
        if start_date:
            query = query.filter(SaleOrm.date_time >= start_date)
        if end_date:
            query = query.filter(SaleOrm.date_time <= end_date)
        
        # Group by customer_id
        query = query.group_by(SaleOrm.customer_id)
        
        # Order by total sales descending
        query = query.order_by(func.sum(SaleOrm.total_amount).desc())
        
        # Apply limit
        if limit:
            query = query.limit(limit)
        
        # Execute and format results
        result = []
        for row in query.all():
            result.append({
                'customer_id': row.customer_id,
                'num_sales': row.num_sales,
                'total_sales': row.total_sales or 0
            })
        
        return result
    
    def get_top_selling_products(self, start_date=None, end_date=None, limit=10):
        """Get top selling products by quantity."""
        from sqlalchemy import func
        
        # Convert dates to datetime if needed
        if start_date and not isinstance(start_date, datetime):
            start_date = datetime.combine(start_date, datetime.min.time())
        if end_date and not isinstance(end_date, datetime):
            end_date = datetime.combine(end_date, datetime.max.time())
        
        # Join query to get product info
        query = self._session.query(
            ProductOrm.id.label('product_id'),
            ProductOrm.code.label('product_code'),
            ProductOrm.description.label('product_description'),
            func.sum(SaleItemOrm.quantity).label('units_sold'),
            func.sum(SaleItemOrm.quantity * SaleItemOrm.unit_price).label('total_sales')
        ).join(
            SaleItemOrm, SaleItemOrm.product_id == ProductOrm.id
        ).join(
            SaleOrm, SaleOrm.id == SaleItemOrm.sale_id
        )
        
        # Apply date filters
        if start_date:
            query = query.filter(SaleOrm.date_time >= start_date)
        if end_date:
            query = query.filter(SaleOrm.date_time <= end_date)
        
        # Group by product
        query = query.group_by(ProductOrm.id, ProductOrm.code, ProductOrm.description)
        
        # Order by units sold descending
        query = query.order_by(func.sum(SaleItemOrm.quantity).desc())
        
        # Apply limit
        if limit:
            query = query.limit(limit)
        
        # Execute and format results
        result = []
        for row in query.all():
            result.append({
                'product_id': row.product_id,
                'product_code': row.product_code,
                'product_description': row.product_description,
                'units_sold': row.units_sold,
                'total_sales': row.total_sales or 0
            })
        
        return result
    
    def calculate_profit_for_period(self, start_date=None, end_date=None):
        """Calculate profit for a period based on cost and sell prices."""
        from sqlalchemy import func
        
        # Convert dates to datetime if needed
        if start_date and not isinstance(start_date, datetime):
            start_date = datetime.combine(start_date, datetime.min.time())
        if end_date and not isinstance(end_date, datetime):
            end_date = datetime.combine(end_date, datetime.max.time())
        
        # Calculate total revenue from sales
        revenue_query = self._session.query(
            func.sum(SaleItemOrm.quantity * SaleItemOrm.unit_price).label('total_revenue')
        ).join(
            SaleOrm, SaleOrm.id == SaleItemOrm.sale_id
        )
        
        # Apply date filters
        if start_date:
            revenue_query = revenue_query.filter(SaleOrm.date_time >= start_date)
        if end_date:
            revenue_query = revenue_query.filter(SaleOrm.date_time <= end_date)
        
        # Calculate total cost from products sold
        cost_query = self._session.query(
            func.sum(SaleItemOrm.quantity * ProductOrm.cost_price).label('total_cost')
        ).join(
            SaleOrm, SaleOrm.id == SaleItemOrm.sale_id
        ).join(
            ProductOrm, ProductOrm.id == SaleItemOrm.product_id
        )
        
        # Apply date filters
        if start_date:
            cost_query = cost_query.filter(SaleOrm.date_time >= start_date)
        if end_date:
            cost_query = cost_query.filter(SaleOrm.date_time <= end_date)
        
        # Execute queries
        revenue_result = revenue_query.scalar() or 0
        cost_result = cost_query.scalar() or 0
        
        # Calculate profit and margin
        profit = revenue_result - cost_result
        margin = (profit / revenue_result) if revenue_result > 0 else 0
        
        return {
            'revenue': revenue_result,
            'cost': cost_result,
            'profit': profit,
            'margin': margin
        }

# Test-specific department repository
class _HelperSqliteDepartmentRepository:
    """SQLite Department Repository for testing."""
    
    def __init__(self, session):
        self._session = session
    
    def add(self, department):
        """Add a new department."""
        try:
            dept_orm = DepartmentOrm()
            dept_orm.name = department.name
            
            self._session.add(dept_orm)
            self._session.flush()
            
            department.id = dept_orm.id
            return department
        except Exception as e:
            self._session.rollback()
            raise ValueError(f"Error adding department: {e}")

# Test-specific product repository
class _HelperSqliteProductRepository:
    """SQLite Product Repository for testing."""
    
    def __init__(self, session):
        self._session = session
    
    def add(self, product):
        """Add a new product."""
        try:
            prod_orm = ProductOrm()
            prod_orm.code = product.code
            prod_orm.description = product.description
            prod_orm.sell_price = float(product.sell_price)
            prod_orm.cost_price = float(product.cost_price) if product.cost_price is not None else None

            # Use quantity_in_stock instead of stock
            prod_orm.quantity_in_stock = float(product.quantity_in_stock or 0.0)
            prod_orm.department_id = product.department_id
            prod_orm.uses_inventory = product.uses_inventory if hasattr(product, 'uses_inventory') else True
            prod_orm.is_active = product.is_active if hasattr(product, 'is_active') else True

            self._session.add(prod_orm)
            self._session.flush()

            product.id = prod_orm.id
            return product
        except Exception as e:
            self._session.rollback()
            raise ValueError(f"Error adding product: {e}")

@pytest.mark.usefixtures("clean_db")
class TestSaleRepository:
    """Test cases for SqliteSaleRepository using pytest fixtures."""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self, clean_db):
        """Set up test data before each test automatically."""
        # Get session from the clean_db fixture
        self.session = clean_db
        
        # Setup repositories
        self.product_repo = _HelperSqliteProductRepository(self.session)
        self.dept_repo = _HelperSqliteDepartmentRepository(self.session)
        
        # Create a dummy department and product for FK constraints
        dept = self.dept_repo.add(Department(name="Test Dept"))
        self.prod1 = self.product_repo.add(Product(code="P001", description="Test Prod 1", sell_price=10.0, department_id=dept.id))
        self.prod2 = self.product_repo.add(Product(code="P002", description="Test Prod 2", sell_price=20.0, department_id=dept.id))
        
        # Yield to allow the test to run
        yield
        
        # No explicit cleanup needed as the clean_db fixture handles this

    def test_add_sale(self, test_db_session):
        """Verify sale header and all associated sale items are saved correctly."""
        sale_repo = _HelperSqliteSaleRepository(test_db_session)

        # 1. Prepare Sale and SaleItem core models
        item1 = SaleItem(
            product_id=self.prod1.id,
            quantity=Decimal("2"),
            unit_price=Decimal("10.00"),
            product_code=self.prod1.code,
            product_description=self.prod1.description
        )
        item2 = SaleItem(
            product_id=self.prod2.id,
            quantity=Decimal("1.5"),
            unit_price=Decimal("20.00"),
            product_code=self.prod2.code,
            product_description=self.prod2.description
        )
        sale_to_add = Sale(items=[item1, item2])
        original_timestamp = sale_to_add.timestamp

        # 2. Call the repository method
        added_sale = sale_repo.add_sale(sale_to_add)

        # 3. Assertions on the returned Sale object
        assert added_sale.id is not None, "Returned sale should have an ID."
        assert added_sale.timestamp == original_timestamp
        assert len(added_sale.items) == 2, "Returned sale should have 2 items."
        assert added_sale.items[0].id is not None, "Returned sale item 1 should have an ID."
        assert added_sale.items[1].id is not None, "Returned sale item 2 should have an ID."
        assert added_sale.items[0].sale_id == added_sale.id, "Item 1 sale_id mismatch."
        assert added_sale.items[1].sale_id == added_sale.id, "Item 2 sale_id mismatch."
        assert added_sale.items[0].product_id == self.prod1.id
        assert added_sale.items[0].quantity == Decimal("2")
        assert added_sale.items[0].unit_price == Decimal("10.00")
        assert added_sale.items[1].product_id == self.prod2.id
        assert added_sale.items[1].quantity == Decimal("1.5")
        assert added_sale.items[1].unit_price == Decimal("20.00")
        assert added_sale.total == Decimal("50.00")  # (2*10) + (1.5*20) = 20 + 30 = 50

        # 4. Verify data in the database directly (optional but recommended)
        sale_orm = test_db_session.get(SaleOrm, added_sale.id)
        assert sale_orm is not None
        
        # SQLAlchemy stores timestamp as datetime, so we need to check date_time
        # which is the column name in the ORM
        assert getattr(sale_orm, 'date_time', None) is not None
        assert abs(sale_orm.total_amount - 50.00) < 0.001

        items_orm = test_db_session.query(SaleItemOrm).filter(SaleItemOrm.sale_id == added_sale.id).order_by(SaleItemOrm.id).all()
        assert len(items_orm) == 2
        assert items_orm[0].product_id == self.prod1.id
        assert abs(items_orm[0].quantity - 2.0) < 0.00001
        assert abs(items_orm[0].unit_price - 10.00) < 0.01
        assert items_orm[0].product_code == self.prod1.code
        assert items_orm[0].product_description == self.prod1.description
        assert items_orm[1].product_id == self.prod2.id
        assert abs(items_orm[1].quantity - 1.5) < 0.00001
        assert abs(items_orm[1].unit_price - 20.00) < 0.01
        assert items_orm[1].product_code == self.prod2.code
        assert items_orm[1].product_description == self.prod2.description

    def test_get_sales_summary_by_period(self, test_db_session):
        """Test get_sales_summary_by_period returns correct aggregation by day."""
        sale_repo = _HelperSqliteSaleRepository(test_db_session)

        # Add two sales on different days
        from datetime import timedelta
        now = datetime.now()
        item1 = SaleItem(
            product_id=self.prod1.id,
            quantity=Decimal("1"),
            unit_price=Decimal("10.00"),
            product_code=self.prod1.code,
            product_description=self.prod1.description
        )
        sale1 = Sale(items=[item1], timestamp=now)
        sale_repo.add_sale(sale1)

        item2 = SaleItem(
            product_id=self.prod2.id,
            quantity=Decimal("2"),
            unit_price=Decimal("20.00"),
            product_code=self.prod2.code,
            product_description=self.prod2.description
        )
        sale2 = Sale(items=[item2], timestamp=now + timedelta(days=1))
        sale_repo.add_sale(sale2)

        # Call the method under test
        summary = sale_repo.get_sales_summary_by_period(
            start_date=now.date(),
            end_date=(now + timedelta(days=1)).date(),
            group_by="day"
        )

        # Should return two entries, one for each day
        assert len(summary) == 2
        # Find the entry for each date
        dates = [entry["date"] for entry in summary]
        totals = [entry["total_sales"] for entry in summary]
        counts = [entry["num_sales"] for entry in summary]
        assert any(abs(total - 10.00) < 0.01 for total in totals)
        assert any(abs(total - 40.00) < 0.01 for total in totals)
        assert sum(counts) == 2

    def test_get_sales_by_payment_type(self, test_db_session):
        """Test get_sales_by_payment_type returns correct aggregation."""
        sale_repo = _HelperSqliteSaleRepository(test_db_session)
        # Add sales with different payment types
        item = SaleItem(
            product_id=self.prod1.id,
            quantity=Decimal("1"),
            unit_price=Decimal("10.00"),
            product_code=self.prod1.code,
            product_description=self.prod1.description
        )
        sale1 = Sale(items=[item], payment_type="Efectivo")
        sale2 = Sale(items=[item], payment_type="Tarjeta")
        sale3 = Sale(items=[item], payment_type="Efectivo")
        sale_repo.add_sale(sale1)
        sale_repo.add_sale(sale2)
        sale_repo.add_sale(sale3)
        result = sale_repo.get_sales_by_payment_type()
        # Should aggregate by payment type
        types = {r["payment_type"]: r["total_sales"] for r in result}
        assert abs(types.get("Efectivo", 0) - 20.0) < 0.01
        assert abs(types.get("Tarjeta", 0) - 10.0) < 0.01

    def test_get_sales_by_department(self, test_db_session):
        """Test get_sales_by_department returns correct aggregation."""
        sale_repo = _HelperSqliteSaleRepository(test_db_session)
        # Add a new department and product
        dept2 = self.dept_repo.add(Department(name="Dept2"))
        prod3 = self.product_repo.add(Product(code="P003", description="Prod 3", sell_price=30.0, department_id=dept2.id))
        # Sale in dept1
        item1 = SaleItem(
            product_id=self.prod1.id,
            quantity=Decimal("2"),
            unit_price=Decimal("10.00"),
            product_code=self.prod1.code,
            product_description=self.prod1.description
        )
        # Sale in dept2
        item2 = SaleItem(
            product_id=prod3.id,
            quantity=Decimal("1"),
            unit_price=Decimal("30.00"),
            product_code=prod3.code,
            product_description=prod3.description
        )
        sale_repo.add_sale(Sale(items=[item1]))
        sale_repo.add_sale(Sale(items=[item2]))
        result = sale_repo.get_sales_by_department()
        # Should aggregate by department
        depts = {r["department_name"]: r["total_sales"] for r in result}
        assert abs(depts.get("Test Dept", 0) - 20.0) < 0.01
        assert abs(depts.get("Dept2", 0) - 30.0) < 0.01

    def test_get_sales_by_customer(self, test_db_session):
        """Test get_sales_by_customer returns correct aggregation."""
        import uuid
        sale_repo = _HelperSqliteSaleRepository(test_db_session)
        # Add sales with different customer UUIDs
        customer_id1 = uuid.uuid4()
        customer_id2 = uuid.uuid4()
        item = SaleItem(
            product_id=self.prod1.id,
            quantity=Decimal("1"),
            unit_price=Decimal("10.00"),
            product_code=self.prod1.code,
            product_description=self.prod1.description
        )
        sale1 = Sale(items=[item], customer_id=customer_id1)
        sale2 = Sale(items=[item], customer_id=customer_id2)
        sale3 = Sale(items=[item], customer_id=customer_id1)
        sale_repo.add_sale(sale1)
        sale_repo.add_sale(sale2)
        sale_repo.add_sale(sale3)
        result = sale_repo.get_sales_by_customer(limit=10)
        # Should aggregate by customer_id (UUID)
        custs = {r["customer_id"]: r["total_sales"] for r in result}
        assert abs(custs.get(customer_id1, 0) - 20.0) < 0.01
        assert abs(custs.get(customer_id2, 0) - 10.0) < 0.01

    def test_get_top_selling_products(self, test_db_session):
        """Test get_top_selling_products returns correct aggregation."""
        sale_repo = _HelperSqliteSaleRepository(test_db_session)
        # Add sales for different products
        item1 = SaleItem(
            product_id=self.prod1.id,
            quantity=Decimal("2"),
            unit_price=Decimal("10.00"),
            product_code=self.prod1.code,
            product_description=self.prod1.description
        )
        item2 = SaleItem(
            product_id=self.prod2.id,
            quantity=Decimal("3"),
            unit_price=Decimal("20.00"),
            product_code=self.prod2.code,
            product_description=self.prod2.description
        )
        sale_repo.add_sale(Sale(items=[item1]))
        sale_repo.add_sale(Sale(items=[item2]))
        result = sale_repo.get_top_selling_products(limit=10)
        # Should aggregate by product
        prods = {r["product_code"]: r["units_sold"] for r in result}
        assert prods.get("P001", 0) == 2
        assert prods.get("P002", 0) == 3

    def test_calculate_profit_for_period(self, test_db_session):
        """Test calculate_profit_for_period returns correct profit calculation."""
        sale_repo = _HelperSqliteSaleRepository(test_db_session)
        # Set up products with cost price 
        # Must update directly in the database to ensure the cost price is set
        product1 = test_db_session.query(ProductOrm).filter(ProductOrm.id == self.prod1.id).first()
        product2 = test_db_session.query(ProductOrm).filter(ProductOrm.id == self.prod2.id).first()
        if product1:
            product1.cost_price = 5.0
        if product2:
            product2.cost_price = 8.0
        test_db_session.flush()
        
        # Sale for prod1 and prod2
        item1 = SaleItem(
            product_id=self.prod1.id,
            quantity=Decimal("2"),
            unit_price=Decimal("10.00"),
            product_code=self.prod1.code,
            product_description=self.prod1.description
        )
        item2 = SaleItem(
            product_id=self.prod2.id,
            quantity=Decimal("1"),
            unit_price=Decimal("20.00"),
            product_code=self.prod2.code,
            product_description=self.prod2.description
        )
        sale_repo.add_sale(Sale(items=[item1, item2]))
        # Call profit calculation
        from datetime import date
        result = sale_repo.calculate_profit_for_period(
            start_date=date.today(),
            end_date=date.today()
        )
        # Should return revenue, cost, profit, margin
        assert "revenue" in result and "cost" in result and "profit" in result and "margin" in result

        assert abs(result["revenue"] - 40.00) < 0.01
        # Cost: (2*5.0) + (1*8.0) = 10 + 8 = 18
        assert abs(result["cost"] - 18.0) < 0.01
        assert abs(result["profit"] - 22.0) < 0.01
        # Margin: profit / revenue
        assert abs(result["margin"] - (22.0 / 40.0)) < 0.01

    def test_get_sale_by_id(self, test_db_session):
        """Test retrieving a single sale by its ID."""
        repo = _HelperSqliteSaleRepository(test_db_session)
        
        # Create a sale to test retrieval (ensures at least one sale exists)
        item = SaleItem(product_id=self.prod1.id, quantity=Decimal("1"), unit_price=Decimal("10.00"), product_code=self.prod1.code, product_description=self.prod1.description)
        test_sale = Sale(items=[item], timestamp=datetime.now())
        repo.add_sale(test_sale)

        # Retrieve using the repository method
        retrieved_sale = repo.get_by_id(test_sale.id)

        assert retrieved_sale is not None
        assert retrieved_sale.id == test_sale.id
        assert retrieved_sale.timestamp == test_sale.timestamp
        assert retrieved_sale.payment_type == test_sale.payment_type
        assert len(retrieved_sale.items) == len(test_sale.items)
        
        # Compare item details (e.g., product codes)
        retrieved_item_codes = sorted([item.product_code for item in retrieved_sale.items])
        test_item_codes = sorted([item.product_code for item in test_sale.items])
        assert retrieved_item_codes == test_item_codes

        # Test retrieving non-existent ID
        non_existent_sale = repo.get_by_id(999999)
        assert non_existent_sale is None

    def test_get_sales_by_period_filtering(self, test_db_session):
        """Test retrieving sales within a specific date/time range."""
        repo = _HelperSqliteSaleRepository(test_db_session)
        
        # Define a period that should capture some, but not all, sales from setup
        start_period = datetime(2023, 10, 26, 10, 0, 0)
        end_period = datetime(2023, 10, 26, 14, 0, 0)

        # Create sample sales for filtering test
        item_in = SaleItem(
            product_id=self.prod1.id,
            quantity=Decimal("1"),
            unit_price=Decimal("10.00"),
            product_code=self.prod1.code,
            product_description=self.prod1.description
        )
        sale_in = Sale(items=[item_in], timestamp=start_period)
        repo.add_sale(sale_in)
        # Sale outside period
        item_out = SaleItem(
            product_id=self.prod2.id,
            quantity=Decimal("1"),
            unit_price=Decimal("20.00"),
            product_code=self.prod2.code,
            product_description=self.prod2.description
        )
        sale_out = Sale(items=[item_out], timestamp=datetime(2023, 10, 26, 15, 0, 0))
        repo.add_sale(sale_out)

        # Retrieve sales within the period
        sales_in_period = repo.get_sales_by_period(start_period, end_period)

        # Assert that we got some sales, but less than the total setup
        all_sales_count = test_db_session.query(SaleOrm).count()
        assert len(sales_in_period) > 0
        assert len(sales_in_period) < all_sales_count

        # Verify all retrieved sales fall within the period
        for sale in sales_in_period:
            assert start_period <= sale.timestamp <= end_period
        
        # Test a period with no sales
        empty_start = datetime(2020, 1, 1, 0, 0, 0)
        empty_end = datetime(2020, 1, 1, 23, 59, 59)
        sales_in_empty_period = repo.get_sales_by_period(empty_start, empty_end)
        assert len(sales_in_empty_period) == 0

if __name__ == '__main__':
    unittest.main()
