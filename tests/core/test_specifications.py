"""
Tests for Specification Pattern

Tests cover:
- Base specification classes
- Product specifications
- Sale specifications
- Specification composition (AND, OR, NOT)
- Repository integration
- SQLAlchemy filter generation
"""

import pytest
from decimal import Decimal
from datetime import datetime
from uuid import uuid4

from core.models.product import Product
from core.models.sale import Sale
from core.specifications.base import (
    Specification,
    ParameterizedSpecification,
    AndSpecification,
    OrSpecification,
    NotSpecification,
)
from core.specifications.product_specifications import (
    ProductInStockSpecification,
    ProductOutOfStockSpecification,
    ProductLowStockSpecification,
    ProductInDepartmentSpecification,
    ProductPriceRangeSpecification,
    ProductCodeLikeSpecification,
    ProductDescriptionLikeSpecification,
    ProductActiveSpecification,
    products_in_stock,
    products_out_of_stock,
    products_low_stock,
    products_in_department,
    products_in_price_range,
    products_code_like,
    products_description_like,
    products_active,
)
from core.specifications.sale_specifications import (
    SaleByDateRangeSpecification,
    SaleByCustomerSpecification,
    SaleByPaymentTypeSpecification,
    SaleAboveAmountSpecification,
    SaleBelowAmountSpecification,
    SaleCreditSaleSpecification,
    SaleByUserSpecification,
    sales_by_date_range,
    sales_by_customer,
    sales_by_payment_type,
    sales_above_amount,
    sales_below_amount,
    credit_sales,
    cash_sales,
    card_sales,
)


class TestBaseSpecification:
    """Tests for base specification classes."""

    def test_specification_interface(self):
        """Test that specifications implement required interface."""

        class TestSpec(Specification[Product]):
            def is_satisfied_by(self, candidate: Product) -> bool:
                return True

            def to_sqlalchemy_filter(self):
                return None

        spec = TestSpec()
        product = Product(code="P001", description="Test")

        assert spec.is_satisfied_by(product)
        assert spec.to_sqlalchemy_filter() is None

    def test_and_composition(self):
        """Test AND composition of specifications."""

        class AlwaysTrueSpec(Specification[Product]):
            def is_satisfied_by(self, candidate: Product) -> bool:
                return True

            def to_sqlalchemy_filter(self):
                return None

        class AlwaysFalseSpec(Specification[Product]):
            def is_satisfied_by(self, candidate: Product) -> bool:
                return False

            def to_sqlalchemy_filter(self):
                return None

        product = Product(code="P001", description="Test")

        # True AND True = True
        spec = AlwaysTrueSpec().and_(AlwaysTrueSpec())
        assert spec.is_satisfied_by(product)

        # True AND False = False
        spec = AlwaysTrueSpec().and_(AlwaysFalseSpec())
        assert not spec.is_satisfied_by(product)

        # False AND False = False
        spec = AlwaysFalseSpec().and_(AlwaysFalseSpec())
        assert not spec.is_satisfied_by(product)

    def test_or_composition(self):
        """Test OR composition of specifications."""

        class AlwaysTrueSpec(Specification[Product]):
            def is_satisfied_by(self, candidate: Product) -> bool:
                return True

            def to_sqlalchemy_filter(self):
                return None

        class AlwaysFalseSpec(Specification[Product]):
            def is_satisfied_by(self, candidate: Product) -> bool:
                return False

            def to_sqlalchemy_filter(self):
                return None

        product = Product(code="P001", description="Test")

        # True OR True = True
        spec = AlwaysTrueSpec().or_(AlwaysTrueSpec())
        assert spec.is_satisfied_by(product)

        # True OR False = True
        spec = AlwaysTrueSpec().or_(AlwaysFalseSpec())
        assert spec.is_satisfied_by(product)

        # False OR False = False
        spec = AlwaysFalseSpec().or_(AlwaysFalseSpec())
        assert not spec.is_satisfied_by(product)

    def test_not_composition(self):
        """Test NOT composition of specifications."""

        class AlwaysTrueSpec(Specification[Product]):
            def is_satisfied_by(self, candidate: Product) -> bool:
                return True

            def to_sqlalchemy_filter(self):
                return None

        class AlwaysFalseSpec(Specification[Product]):
            def is_satisfied_by(self, candidate: Product) -> bool:
                return False

            def to_sqlalchemy_filter(self):
                return None

        product = Product(code="P001", description="Test")

        # NOT True = False
        spec = AlwaysTrueSpec().not_()
        assert not spec.is_satisfied_by(product)

        # NOT False = True
        spec = AlwaysFalseSpec().not_()
        assert spec.is_satisfied_by(product)

    def test_complex_composition(self):
        """Test complex composition with multiple operators."""

        class InStockSpec(Specification[Product]):
            def is_satisfied_by(self, candidate: Product) -> bool:
                return candidate.quantity_in_stock > 0

            def to_sqlalchemy_filter(self):
                return None

        class ExpensiveSpec(Specification[Product]):
            def is_satisfied_by(self, candidate: Product) -> bool:
                return candidate.sell_price > Decimal("100")

            def to_sqlalchemy_filter(self):
                return None

        # (in_stock AND expensive) OR out_of_stock
        in_stock = InStockSpec()
        expensive = ExpensiveSpec()

        # Product: in stock, expensive -> should match
        product1 = Product(
            code="P001",
            description="Test",
            quantity_in_stock=Decimal("10"),
            sell_price=Decimal("150"),
        )

        spec = in_stock.and_(expensive)
        assert spec.is_satisfied_by(product1)

        # Product: in stock, not expensive -> should not match
        product2 = Product(
            code="P002",
            description="Test",
            quantity_in_stock=Decimal("10"),
            sell_price=Decimal("50"),
        )

        assert not spec.is_satisfied_by(product2)


class TestProductSpecifications:
    """Tests for product specifications."""

    def test_product_in_stock_satisfied(self):
        """Test product in stock specification - satisfied case."""
        spec = products_in_stock()

        product = Product(
            code="P001", description="Test Product", quantity_in_stock=Decimal("10")
        )

        assert spec.is_satisfied_by(product)

    def test_product_in_stock_not_satisfied(self):
        """Test product in stock specification - not satisfied case."""
        spec = products_in_stock()

        product = Product(
            code="P001", description="Test Product", quantity_in_stock=Decimal("0")
        )

        assert not spec.is_satisfied_by(product)

    def test_product_out_of_stock_satisfied(self):
        """Test product out of stock specification."""
        spec = products_out_of_stock()

        product = Product(
            code="P001", description="Test Product", quantity_in_stock=Decimal("0")
        )

        assert spec.is_satisfied_by(product)

    def test_product_low_stock_satisfied(self):
        """Test product low stock specification - satisfied case."""
        spec = products_low_stock()

        product = Product(
            code="P001",
            description="Test Product",
            quantity_in_stock=Decimal("5"),
            min_stock=Decimal("10"),
        )

        assert spec.is_satisfied_by(product)

    def test_product_low_stock_not_satisfied(self):
        """Test product low stock specification - not satisfied case."""
        spec = products_low_stock()

        # Product with adequate stock
        product1 = Product(
            code="P001",
            description="Test Product",
            quantity_in_stock=Decimal("15"),
            min_stock=Decimal("10"),
        )
        assert not spec.is_satisfied_by(product1)

        # Product without min_stock setting
        product2 = Product(
            code="P002",
            description="Test Product",
            quantity_in_stock=Decimal("5"),
            min_stock=None,
        )
        assert not spec.is_satisfied_by(product2)

    def test_product_in_department_satisfied(self):
        """Test product in department specification."""
        dept_id = uuid4()
        spec = products_in_department(dept_id)

        product = Product(
            code="P001",
            description="Test Product",
            department_id=dept_id,
        )

        assert spec.is_satisfied_by(product)

    def test_product_in_department_not_satisfied(self):
        """Test product in department specification - wrong department."""
        dept_id = uuid4()
        other_dept_id = uuid4()
        spec = products_in_department(dept_id)

        product = Product(
            code="P001",
            description="Test Product",
            department_id=other_dept_id,
        )

        assert not spec.is_satisfied_by(product)

    def test_product_price_range_both_bounds(self):
        """Test price range specification with both min and max."""
        spec = products_in_price_range(
            min_price=Decimal("10"), max_price=Decimal("100")
        )

        # Within range
        product1 = Product(
            code="P001", description="Test", sell_price=Decimal("50")
        )
        assert spec.is_satisfied_by(product1)

        # Below range
        product2 = Product(code="P002", description="Test", sell_price=Decimal("5"))
        assert not spec.is_satisfied_by(product2)

        # Above range
        product3 = Product(
            code="P003", description="Test", sell_price=Decimal("150")
        )
        assert not spec.is_satisfied_by(product3)

        # At boundaries
        product4 = Product(
            code="P004", description="Test", sell_price=Decimal("10")
        )
        assert spec.is_satisfied_by(product4)

        product5 = Product(
            code="P005", description="Test", sell_price=Decimal("100")
        )
        assert spec.is_satisfied_by(product5)

    def test_product_price_range_min_only(self):
        """Test price range specification with only minimum."""
        spec = products_in_price_range(min_price=Decimal("50"))

        product1 = Product(
            code="P001", description="Test", sell_price=Decimal("100")
        )
        assert spec.is_satisfied_by(product1)

        product2 = Product(
            code="P002", description="Test", sell_price=Decimal("25")
        )
        assert not spec.is_satisfied_by(product2)

    def test_product_price_range_max_only(self):
        """Test price range specification with only maximum."""
        spec = products_in_price_range(max_price=Decimal("100"))

        product1 = Product(
            code="P001", description="Test", sell_price=Decimal("50")
        )
        assert spec.is_satisfied_by(product1)

        product2 = Product(
            code="P002", description="Test", sell_price=Decimal("150")
        )
        assert not spec.is_satisfied_by(product2)

    def test_product_code_like(self):
        """Test product code like specification."""
        spec = products_code_like("ABC")

        product1 = Product(code="ABC123", description="Test")
        assert spec.is_satisfied_by(product1)

        product2 = Product(code="XYZABC", description="Test")
        assert spec.is_satisfied_by(product2)

        product3 = Product(code="XYZ123", description="Test")
        assert not spec.is_satisfied_by(product3)

    def test_product_code_like_case_insensitive(self):
        """Test product code like is case insensitive."""
        spec = products_code_like("abc")

        product = Product(code="ABC123", description="Test")
        assert spec.is_satisfied_by(product)

    def test_product_description_like(self):
        """Test product description like specification."""
        spec = products_description_like("laptop")

        product1 = Product(code="P001", description="Dell Laptop 15 inch")
        assert spec.is_satisfied_by(product1)

        product2 = Product(code="P002", description="Desktop Computer")
        assert not spec.is_satisfied_by(product2)

    def test_product_active(self):
        """Test product active specification."""
        spec = products_active()

        product1 = Product(code="P001", description="Test", is_active=True)
        assert spec.is_satisfied_by(product1)

        product2 = Product(code="P002", description="Test", is_active=False)
        assert not spec.is_satisfied_by(product2)

    def test_product_specification_composition(self):
        """Test composing multiple product specifications."""
        dept_id = uuid4()

        # in_stock AND in_department AND price <= 100
        spec = (
            products_in_stock()
            .and_(products_in_department(dept_id))
            .and_(products_in_price_range(max_price=Decimal("100")))
        )

        # Matches all criteria
        product1 = Product(
            code="P001",
            description="Test",
            quantity_in_stock=Decimal("10"),
            department_id=dept_id,
            sell_price=Decimal("50"),
        )
        assert spec.is_satisfied_by(product1)

        # Doesn't match: out of stock
        product2 = Product(
            code="P002",
            description="Test",
            quantity_in_stock=Decimal("0"),
            department_id=dept_id,
            sell_price=Decimal("50"),
        )
        assert not spec.is_satisfied_by(product2)

        # Doesn't match: wrong department
        product3 = Product(
            code="P003",
            description="Test",
            quantity_in_stock=Decimal("10"),
            department_id=uuid4(),
            sell_price=Decimal("50"),
        )
        assert not spec.is_satisfied_by(product3)

        # Doesn't match: too expensive
        product4 = Product(
            code="P004",
            description="Test",
            quantity_in_stock=Decimal("10"),
            department_id=dept_id,
            sell_price=Decimal("150"),
        )
        assert not spec.is_satisfied_by(product4)


class TestSaleSpecifications:
    """Tests for sale specifications."""

    def test_sale_by_date_range_satisfied(self):
        """Test sale by date range specification - satisfied case."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        spec = sales_by_date_range(start, end)

        sale = Sale(
            created_at=datetime(2024, 1, 15),
            total=Decimal("100"),
            payment_type="cash",
        )

        assert spec.is_satisfied_by(sale)

    def test_sale_by_date_range_not_satisfied(self):
        """Test sale by date range specification - not satisfied case."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        spec = sales_by_date_range(start, end)

        # Before range
        sale1 = Sale(
            created_at=datetime(2023, 12, 31),
            total=Decimal("100"),
            payment_type="cash",
        )
        assert not spec.is_satisfied_by(sale1)

        # After range
        sale2 = Sale(
            created_at=datetime(2024, 2, 1),
            total=Decimal("100"),
            payment_type="cash",
        )
        assert not spec.is_satisfied_by(sale2)

    def test_sale_by_date_range_boundaries(self):
        """Test sale by date range specification - boundary cases."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        end = datetime(2024, 1, 31, 23, 59, 59)
        spec = sales_by_date_range(start, end)

        # At start boundary
        sale1 = Sale(
            created_at=start,
            total=Decimal("100"),
            payment_type="cash",
        )
        assert spec.is_satisfied_by(sale1)

        # At end boundary
        sale2 = Sale(
            created_at=end,
            total=Decimal("100"),
            payment_type="cash",
        )
        assert spec.is_satisfied_by(sale2)

    def test_sale_by_customer_satisfied(self):
        """Test sale by customer specification."""
        customer_id = uuid4()
        spec = sales_by_customer(customer_id)

        sale = Sale(
            customer_id=customer_id,
            total=Decimal("100"),
            payment_type="credit",
        )

        assert spec.is_satisfied_by(sale)

    def test_sale_by_customer_not_satisfied(self):
        """Test sale by customer specification - wrong customer."""
        customer_id = uuid4()
        other_customer_id = uuid4()
        spec = sales_by_customer(customer_id)

        sale = Sale(
            customer_id=other_customer_id,
            total=Decimal("100"),
            payment_type="credit",
        )

        assert not spec.is_satisfied_by(sale)

    def test_sale_by_payment_type(self):
        """Test sale by payment type specification."""
        spec = sales_by_payment_type("cash")

        sale1 = Sale(total=Decimal("100"), payment_type="cash")
        assert spec.is_satisfied_by(sale1)

        sale2 = Sale(total=Decimal("100"), payment_type="credit")
        assert not spec.is_satisfied_by(sale2)

    def test_sale_above_amount_satisfied(self):
        """Test sale above amount specification."""
        spec = sales_above_amount(Decimal("100"))

        sale1 = Sale(total=Decimal("150"), payment_type="cash")
        assert spec.is_satisfied_by(sale1)

        sale2 = Sale(total=Decimal("100"), payment_type="cash")
        assert not spec.is_satisfied_by(sale2)

        sale3 = Sale(total=Decimal("50"), payment_type="cash")
        assert not spec.is_satisfied_by(sale3)

    def test_sale_below_amount_satisfied(self):
        """Test sale below amount specification."""
        spec = sales_below_amount(Decimal("100"))

        sale1 = Sale(total=Decimal("50"), payment_type="cash")
        assert spec.is_satisfied_by(sale1)

        sale2 = Sale(total=Decimal("100"), payment_type="cash")
        assert not spec.is_satisfied_by(sale2)

        sale3 = Sale(total=Decimal("150"), payment_type="cash")
        assert not spec.is_satisfied_by(sale3)

    def test_credit_sales_specification(self):
        """Test credit sales specification."""
        spec = credit_sales()

        sale1 = Sale(total=Decimal("100"), payment_type="credit")
        assert spec.is_satisfied_by(sale1)

        sale2 = Sale(total=Decimal("100"), payment_type="cash")
        assert not spec.is_satisfied_by(sale2)

    def test_cash_sales_specification(self):
        """Test cash sales specification."""
        spec = cash_sales()

        sale1 = Sale(total=Decimal("100"), payment_type="cash")
        assert spec.is_satisfied_by(sale1)

        sale2 = Sale(total=Decimal("100"), payment_type="credit")
        assert not spec.is_satisfied_by(sale2)

    def test_card_sales_specification(self):
        """Test card sales specification."""
        spec = card_sales()

        sale1 = Sale(total=Decimal("100"), payment_type="card")
        assert spec.is_satisfied_by(sale1)

        sale2 = Sale(total=Decimal("100"), payment_type="cash")
        assert not spec.is_satisfied_by(sale2)

    def test_sale_by_user_specification(self):
        """Test sale by user specification."""
        user_id = uuid4()
        spec = SaleByUserSpecification(user_id)

        sale1 = Sale(
            user_id=user_id,
            total=Decimal("100"),
            payment_type="cash",
        )
        assert spec.is_satisfied_by(sale1)

        sale2 = Sale(
            user_id=uuid4(),
            total=Decimal("100"),
            payment_type="cash",
        )
        assert not spec.is_satisfied_by(sale2)

    def test_sale_specification_composition(self):
        """Test composing multiple sale specifications."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)

        # credit sales in January above $500
        spec = (
            sales_by_date_range(start, end)
            .and_(credit_sales())
            .and_(sales_above_amount(Decimal("500")))
        )

        # Matches all criteria
        sale1 = Sale(
            created_at=datetime(2024, 1, 15),
            total=Decimal("1000"),
            payment_type="credit",
        )
        assert spec.is_satisfied_by(sale1)

        # Doesn't match: wrong date
        sale2 = Sale(
            created_at=datetime(2024, 2, 1),
            total=Decimal("1000"),
            payment_type="credit",
        )
        assert not spec.is_satisfied_by(sale2)

        # Doesn't match: not credit
        sale3 = Sale(
            created_at=datetime(2024, 1, 15),
            total=Decimal("1000"),
            payment_type="cash",
        )
        assert not spec.is_satisfied_by(sale3)

        # Doesn't match: too small
        sale4 = Sale(
            created_at=datetime(2024, 1, 15),
            total=Decimal("100"),
            payment_type="credit",
        )
        assert not spec.is_satisfied_by(sale4)


class TestSQLAlchemyFilterGeneration:
    """Tests for SQLAlchemy filter generation."""

    def test_product_in_stock_filter(self):
        """Test that product in stock generates valid SQLAlchemy filter."""
        spec = products_in_stock()
        filter_expr = spec.to_sqlalchemy_filter()

        assert filter_expr is not None
        # Further testing would require SQLAlchemy setup

    def test_composite_filter_generation(self):
        """Test that composite specifications generate valid filters."""
        spec = products_in_stock().and_(products_active())
        filter_expr = spec.to_sqlalchemy_filter()

        assert filter_expr is not None
        # Further testing would require SQLAlchemy setup


class TestSpecificationRepresentation:
    """Tests for specification string representation."""

    def test_product_in_stock_repr(self):
        """Test string representation of product in stock spec."""
        spec = products_in_stock()
        assert repr(spec) == "ProductInStock"

    def test_product_in_department_repr(self):
        """Test string representation of parameterized spec."""
        dept_id = uuid4()
        spec = products_in_department(dept_id)
        assert f"ProductInDepartment({dept_id})" == repr(spec)

    def test_composite_repr(self):
        """Test string representation of composite spec."""
        spec = products_in_stock().and_(products_active())
        assert "AND" in repr(spec)
        assert "ProductInStock" in repr(spec)
        assert "ProductActive" in repr(spec)


class TestInMemoryRepository:
    """Tests for in-memory specification repository."""

    def test_in_memory_repository_find_by_specification(self):
        """Test finding items by specification in memory."""
        from core.interfaces.specification_repository import (
            InMemorySpecificationRepository,
        )

        repo = InMemorySpecificationRepository[Product]()

        # Add products
        product1 = Product(
            code="P001", description="Test 1", quantity_in_stock=Decimal("10")
        )
        product2 = Product(
            code="P002", description="Test 2", quantity_in_stock=Decimal("0")
        )
        product3 = Product(
            code="P003", description="Test 3", quantity_in_stock=Decimal("5")
        )

        repo.add(product1)
        repo.add(product2)
        repo.add(product3)

        # Find in-stock products
        spec = products_in_stock()
        results = repo.find_by_specification(spec)

        assert len(results) == 2
        assert product1 in results
        assert product3 in results
        assert product2 not in results

    def test_in_memory_repository_count(self):
        """Test counting items by specification."""
        from core.interfaces.specification_repository import (
            InMemorySpecificationRepository,
        )

        repo = InMemorySpecificationRepository[Product]()

        product1 = Product(code="P001", quantity_in_stock=Decimal("10"))
        product2 = Product(code="P002", quantity_in_stock=Decimal("0"))

        repo.add(product1)
        repo.add(product2)

        spec = products_in_stock()
        count = repo.count_by_specification(spec)

        assert count == 1

    def test_in_memory_repository_exists(self):
        """Test checking existence by specification."""
        from core.interfaces.specification_repository import (
            InMemorySpecificationRepository,
        )

        repo = InMemorySpecificationRepository[Product]()

        product = Product(code="P001", quantity_in_stock=Decimal("0"))
        repo.add(product)

        in_stock_spec = products_in_stock()
        out_of_stock_spec = products_out_of_stock()

        assert not repo.exists_by_specification(in_stock_spec)
        assert repo.exists_by_specification(out_of_stock_spec)

    def test_in_memory_repository_find_one(self):
        """Test finding first item by specification."""
        from core.interfaces.specification_repository import (
            InMemorySpecificationRepository,
        )

        repo = InMemorySpecificationRepository[Product]()

        product1 = Product(code="P001", quantity_in_stock=Decimal("10"))
        product2 = Product(code="P002", quantity_in_stock=Decimal("20"))

        repo.add(product1)
        repo.add(product2)

        spec = products_in_stock()
        result = repo.find_one_by_specification(spec)

        assert result is not None
        assert result.code in ["P001", "P002"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
