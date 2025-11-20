"""
Tests for Value Objects

Tests cover:
- Base value object functionality
- Money value object
- Address value object
- Email value object
- PhoneNumber value object
- TaxId value object
- ProductCode value object
- Percentage value object
- Validation
- Immutability
- Equality
"""

import pytest
from decimal import Decimal
from dataclasses import FrozenInstanceError

from core.value_objects.base import (
    ValueObject,
    ValidationError,
    validate_not_empty,
    validate_positive,
    validate_non_negative,
    validate_range,
    validate_length,
)
from core.value_objects.money import Money
from core.value_objects.address import Address
from core.value_objects.email import Email
from core.value_objects.phone_number import PhoneNumber
from core.value_objects.tax_id import TaxId
from core.value_objects.product_code import ProductCode
from core.value_objects.percentage import Percentage


class TestValidationHelpers:
    """Tests for validation helper functions."""

    def test_validate_not_empty_with_valid_string(self):
        """Test validate_not_empty with valid string."""
        validate_not_empty("test", "field")  # Should not raise

    def test_validate_not_empty_with_empty_string(self):
        """Test validate_not_empty with empty string."""
        with pytest.raises(ValidationError):
            validate_not_empty("", "field")

    def test_validate_not_empty_with_whitespace(self):
        """Test validate_not_empty with whitespace."""
        with pytest.raises(ValidationError):
            validate_not_empty("   ", "field")

    def test_validate_positive_with_positive_number(self):
        """Test validate_positive with positive number."""
        validate_positive(10, "field")  # Should not raise

    def test_validate_positive_with_zero(self):
        """Test validate_positive with zero."""
        with pytest.raises(ValidationError):
            validate_positive(0, "field")

    def test_validate_positive_with_negative(self):
        """Test validate_positive with negative."""
        with pytest.raises(ValidationError):
            validate_positive(-10, "field")

    def test_validate_non_negative_with_positive(self):
        """Test validate_non_negative with positive."""
        validate_non_negative(10, "field")  # Should not raise

    def test_validate_non_negative_with_zero(self):
        """Test validate_non_negative with zero."""
        validate_non_negative(0, "field")  # Should not raise

    def test_validate_non_negative_with_negative(self):
        """Test validate_non_negative with negative."""
        with pytest.raises(ValidationError):
            validate_non_negative(-10, "field")

    def test_validate_range_within_range(self):
        """Test validate_range with value in range."""
        validate_range(5, 0, 10, "field")  # Should not raise

    def test_validate_range_at_boundaries(self):
        """Test validate_range at boundaries."""
        validate_range(0, 0, 10, "field")  # Should not raise
        validate_range(10, 0, 10, "field")  # Should not raise

    def test_validate_range_outside_range(self):
        """Test validate_range outside range."""
        with pytest.raises(ValidationError):
            validate_range(-1, 0, 10, "field")

        with pytest.raises(ValidationError):
            validate_range(11, 0, 10, "field")

    def test_validate_length_valid(self):
        """Test validate_length with valid string."""
        validate_length("test", 1, 10, "field")  # Should not raise

    def test_validate_length_too_short(self):
        """Test validate_length too short."""
        with pytest.raises(ValidationError):
            validate_length("a", 2, 10, "field")

    def test_validate_length_too_long(self):
        """Test validate_length too long."""
        with pytest.raises(ValidationError):
            validate_length("a" * 11, 1, 10, "field")


class TestMoney:
    """Tests for Money value object."""

    def test_create_valid_money(self):
        """Test creating valid money."""
        money = Money(Decimal("10.50"), "USD")
        assert money.amount == Decimal("10.50")
        assert money.currency == "USD"

    def test_create_money_from_int(self):
        """Test creating money from int (converts to Decimal)."""
        money = Money(10, "USD")
        assert money.amount == Decimal("10")

    def test_create_money_normalizes_currency(self):
        """Test that currency is normalized to uppercase."""
        money = Money(Decimal("10"), "usd")
        assert money.currency == "USD"

    def test_negative_amount_raises_error(self):
        """Test that negative amount raises error."""
        with pytest.raises(ValidationError):
            Money(Decimal("-10"), "USD")

    def test_invalid_currency_raises_error(self):
        """Test that invalid currency raises error."""
        with pytest.raises(ValidationError):
            Money(Decimal("10"), "INVALID")

        with pytest.raises(ValidationError):
            Money(Decimal("10"), "US")  # Too short

    def test_add_same_currency(self):
        """Test adding money with same currency."""
        m1 = Money(Decimal("10"), "USD")
        m2 = Money(Decimal("5"), "USD")
        result = m1.add(m2)

        assert result.amount == Decimal("15")
        assert result.currency == "USD"

    def test_add_different_currency_raises_error(self):
        """Test that adding different currencies raises error."""
        m1 = Money(Decimal("10"), "USD")
        m2 = Money(Decimal("5"), "EUR")

        with pytest.raises(ValidationError):
            m1.add(m2)

    def test_subtract(self):
        """Test subtracting money."""
        m1 = Money(Decimal("10"), "USD")
        m2 = Money(Decimal("3"), "USD")
        result = m1.subtract(m2)

        assert result.amount == Decimal("7")

    def test_subtract_resulting_in_negative_raises_error(self):
        """Test that subtraction resulting in negative raises error."""
        m1 = Money(Decimal("5"), "USD")
        m2 = Money(Decimal("10"), "USD")

        with pytest.raises(ValidationError):
            m1.subtract(m2)

    def test_multiply(self):
        """Test multiplying money by scalar."""
        money = Money(Decimal("10"), "USD")
        result = money.multiply(2)

        assert result.amount == Decimal("20")

        result = money.multiply(Decimal("1.5"))
        assert result.amount == Decimal("15")

    def test_divide(self):
        """Test dividing money by scalar."""
        money = Money(Decimal("10"), "USD")
        result = money.divide(2)

        assert result.amount == Decimal("5")

    def test_divide_by_zero_raises_error(self):
        """Test that division by zero raises error."""
        money = Money(Decimal("10"), "USD")

        with pytest.raises(ValidationError):
            money.divide(0)

    def test_round(self):
        """Test rounding money."""
        money = Money(Decimal("10.556"), "USD")
        rounded = money.round(2)

        assert rounded.amount == Decimal("10.56")

    def test_allocate(self):
        """Test allocating money by ratios."""
        money = Money(Decimal("100"), "USD")
        shares = money.allocate([1, 1, 1])  # Split 3 ways

        assert len(shares) == 3
        # Check total is preserved (no rounding loss)
        total = sum((s.amount for s in shares), Decimal("0"))
        assert total == Decimal("100")

    def test_convert_to(self):
        """Test currency conversion."""
        usd = Money(Decimal("100"), "USD")
        eur = usd.convert_to("EUR", Decimal("0.85"))

        assert eur.amount == Decimal("85")
        assert eur.currency == "EUR"

    def test_is_zero(self):
        """Test is_zero method."""
        assert Money.zero("USD").is_zero()
        assert not Money(Decimal("1"), "USD").is_zero()

    def test_is_positive(self):
        """Test is_positive method."""
        assert Money(Decimal("1"), "USD").is_positive()
        assert not Money.zero("USD").is_positive()

    def test_comparison_operators(self):
        """Test comparison operators."""
        m1 = Money(Decimal("10"), "USD")
        m2 = Money(Decimal("20"), "USD")
        m3 = Money(Decimal("10"), "USD")

        assert m1 < m2
        assert m1 <= m2
        assert m1 <= m3
        assert m2 > m1
        assert m2 >= m1
        assert m1 >= m3

    def test_equality(self):
        """Test value equality."""
        m1 = Money(Decimal("10"), "USD")
        m2 = Money(Decimal("10"), "USD")
        m3 = Money(Decimal("5"), "USD")

        assert m1 == m2  # Same value
        assert m1 is not m2  # Different objects
        assert m1 != m3  # Different value

    def test_immutability(self):
        """Test that money is immutable."""
        money = Money(Decimal("10"), "USD")

        with pytest.raises((AttributeError, FrozenInstanceError)):
            money.amount = Decimal("20")

    def test_str_representation(self):
        """Test string representation."""
        money = Money(Decimal("10.50"), "USD")
        assert str(money) == "USD 10.50"

    def test_from_float(self):
        """Test creating from float."""
        money = Money.from_float(10.50, "USD")
        assert money.amount == Decimal("10.50")

    def test_from_string(self):
        """Test creating from string."""
        money = Money.from_string("10.50", "USD")
        assert money.amount == Decimal("10.50")


class TestAddress:
    """Tests for Address value object."""

    def test_create_valid_address(self):
        """Test creating valid address."""
        address = Address(
            street="123 Main St",
            city="Springfield",
            state="IL",
            postal_code="62701",
            country="USA",
        )

        assert address.street == "123 Main St"
        assert address.city == "Springfield"
        assert address.state == "IL"
        assert address.postal_code == "62701"
        assert address.country == "USA"

    def test_create_address_with_apartment(self):
        """Test creating address with apartment."""
        address = Address(
            street="123 Main St",
            city="Springfield",
            state="IL",
            postal_code="62701",
            country="USA",
            apartment="Apt 4B",
        )

        assert address.apartment == "Apt 4B"

    def test_empty_street_raises_error(self):
        """Test that empty street raises error."""
        with pytest.raises(ValidationError):
            Address(
                street="",
                city="Springfield",
                postal_code="62701",
                country="USA",
            )

    def test_str_representation(self):
        """Test string representation."""
        address = Address(
            street="123 Main St",
            city="Springfield",
            state="IL",
            postal_code="62701",
            country="USA",
        )

        assert str(address) == "123 Main St, Springfield, IL 62701, USA"

    def test_str_with_apartment(self):
        """Test string representation with apartment."""
        address = Address(
            street="123 Main St",
            city="Springfield",
            postal_code="62701",
            country="USA",
            apartment="Apt 4B",
        )

        assert "Apt 4B" in str(address)

    def test_to_multiline(self):
        """Test multiline formatting."""
        address = Address(
            street="123 Main St",
            city="Springfield",
            state="IL",
            postal_code="62701",
            country="USA",
        )

        multiline = address.to_multiline()
        assert "123 Main St" in multiline
        assert "Springfield, IL 62701" in multiline
        assert "USA" in multiline

    def test_is_in_country(self):
        """Test is_in_country method."""
        address = Address(
            street="123 Main St",
            city="Springfield",
            postal_code="62701",
            country="USA",
        )

        assert address.is_in_country("USA")
        assert address.is_in_country("usa")  # Case insensitive
        assert not address.is_in_country("Canada")

    def test_is_in_state(self):
        """Test is_in_state method."""
        address = Address(
            street="123 Main St",
            city="Springfield",
            state="IL",
            postal_code="62701",
            country="USA",
        )

        assert address.is_in_state("IL")
        assert address.is_in_state("il")  # Case insensitive
        assert not address.is_in_state("CA")

    def test_is_in_city(self):
        """Test is_in_city method."""
        address = Address(
            street="123 Main St",
            city="Springfield",
            postal_code="62701",
            country="USA",
        )

        assert address.is_in_city("Springfield")
        assert not address.is_in_city("Chicago")

    def test_create_simple(self):
        """Test create_simple factory method."""
        address = Address.create_simple(
            "123 Main St", "Springfield", "62701"
        )

        assert address.street == "123 Main St"
        assert address.country == "USA"  # Default
        assert address.state is None


class TestEmail:
    """Tests for Email value object."""

    def test_create_valid_email(self):
        """Test creating valid email."""
        email = Email("test@example.com")
        assert email.value == "test@example.com"

    def test_email_normalized_to_lowercase(self):
        """Test that email is normalized to lowercase."""
        email = Email("TEST@EXAMPLE.COM")
        assert email.value == "test@example.com"

    def test_invalid_email_raises_error(self):
        """Test that invalid email raises error."""
        with pytest.raises(ValidationError):
            Email("not-an-email")

        with pytest.raises(ValidationError):
            Email("@example.com")

        with pytest.raises(ValidationError):
            Email("test@")

    def test_empty_email_raises_error(self):
        """Test that empty email raises error."""
        with pytest.raises(ValidationError):
            Email("")

    def test_local_part(self):
        """Test local_part property."""
        email = Email("john.doe@example.com")
        assert email.local_part == "john.doe"

    def test_domain(self):
        """Test domain property."""
        email = Email("john@example.com")
        assert email.domain == "example.com"

    def test_is_from_domain(self):
        """Test is_from_domain method."""
        email = Email("john@example.com")

        assert email.is_from_domain("example.com")
        assert email.is_from_domain("EXAMPLE.COM")  # Case insensitive
        assert not email.is_from_domain("other.com")

    def test_obfuscate(self):
        """Test obfuscate method."""
        email = Email("john.doe@example.com")
        obfuscated = email.obfuscate()

        assert "***" in obfuscated
        assert "@example.com" in obfuscated

    def test_is_valid_email_static_method(self):
        """Test is_valid_email static method."""
        assert Email.is_valid_email("test@example.com")
        assert not Email.is_valid_email("invalid")

    def test_equality(self):
        """Test email equality."""
        e1 = Email("test@example.com")
        e2 = Email("TEST@EXAMPLE.COM")  # Normalized to lowercase

        assert e1 == e2


class TestPhoneNumber:
    """Tests for PhoneNumber value object."""

    def test_create_valid_phone(self):
        """Test creating valid phone number."""
        phone = PhoneNumber("+15551234567")
        assert phone.value == "+15551234567"

    def test_create_phone_various_formats(self):
        """Test creating phone with various formats."""
        formats = [
            "+1-555-123-4567",
            "(555) 123-4567",
            "555.123.4567",
            "5551234567",
        ]

        for fmt in formats:
            phone = PhoneNumber(fmt)
            assert phone.digits  # Has digits

    def test_invalid_phone_raises_error(self):
        """Test that invalid phone raises error."""
        with pytest.raises(ValidationError):
            PhoneNumber("abc123")

        with pytest.raises(ValidationError):
            PhoneNumber("123")  # Too short

    def test_digits_property(self):
        """Test digits property."""
        phone = PhoneNumber("+1-555-123-4567")
        assert phone.digits == "15551234567"

    def test_country_code_property(self):
        """Test country_code property."""
        phone = PhoneNumber("+15551234567")
        assert phone.country_code == "1"

    def test_format_international(self):
        """Test international formatting."""
        phone = PhoneNumber("+15551234567")
        formatted = phone.format("international")

        assert "555" in formatted
        assert "123" in formatted
        assert "4567" in formatted

    def test_format_national(self):
        """Test national formatting."""
        phone = PhoneNumber("+15551234567")
        formatted = phone.format("national")

        assert "555" in formatted

    def test_format_compact(self):
        """Test compact formatting."""
        phone = PhoneNumber("+1-555-123-4567")
        formatted = phone.format("compact")

        assert formatted == "+15551234567"

    def test_from_parts(self):
        """Test from_parts factory method."""
        phone = PhoneNumber.from_parts("555", "123", "4567")

        assert "555" in phone.digits
        assert "123" in phone.digits
        assert "4567" in phone.digits

    def test_is_valid_phone_static_method(self):
        """Test is_valid_phone static method."""
        assert PhoneNumber.is_valid_phone("+15551234567")
        assert not PhoneNumber.is_valid_phone("invalid")


class TestTaxId:
    """Tests for TaxId value object."""

    def test_create_valid_cuit(self):
        """Test creating valid CUIT."""
        # Note: This uses a valid check digit
        cuit = TaxId("20-12345678-9")
        assert cuit.digits == "20123456789"

    def test_invalid_cuit_raises_error(self):
        """Test that invalid CUIT raises error."""
        with pytest.raises(ValidationError):
            TaxId("12-345")  # Too short

        with pytest.raises(ValidationError):
            TaxId("abc-12345678-9")  # Non-numeric

    def test_type_code_property(self):
        """Test type_code property."""
        cuit = TaxId("20-12345678-9")
        assert cuit.type_code == "20"

    def test_document_number_property(self):
        """Test document_number property."""
        cuit = TaxId("20-12345678-9")
        assert cuit.document_number == "12345678"

    def test_check_digit_property(self):
        """Test check_digit property."""
        cuit = TaxId("20-12345678-9")
        assert cuit.check_digit == "9"

    def test_format(self):
        """Test formatting."""
        cuit = TaxId("20123456789")
        assert cuit.format() == "20-12345678-9"
        assert cuit.format("/") == "20/12345678/9"

    def test_str_representation(self):
        """Test string representation."""
        cuit = TaxId("20123456789")
        assert str(cuit) == "20-12345678-9"


class TestProductCode:
    """Tests for ProductCode value object."""

    def test_create_valid_code(self):
        """Test creating valid product code."""
        code = ProductCode("ABC-123")
        assert code.value == "ABC-123"

    def test_code_normalized_to_uppercase(self):
        """Test that code is normalized to uppercase."""
        code = ProductCode("abc-123")
        assert code.value == "ABC-123"

    def test_invalid_characters_raise_error(self):
        """Test that invalid characters raise error."""
        with pytest.raises(ValidationError):
            ProductCode("ABC@123")  # @ not allowed

        with pytest.raises(ValidationError):
            ProductCode("ABC 123")  # Space not allowed

    def test_empty_code_raises_error(self):
        """Test that empty code raises error."""
        with pytest.raises(ValidationError):
            ProductCode("")

    def test_prefix_property(self):
        """Test prefix property."""
        code = ProductCode("ABC-123")
        assert code.prefix == "ABC"

    def test_suffix_property(self):
        """Test suffix property."""
        code = ProductCode("ABC-123")
        assert code.suffix == "123"

    def test_has_prefix(self):
        """Test has_prefix method."""
        code = ProductCode("ABC-123")

        assert code.has_prefix("ABC")
        assert code.has_prefix("abc")  # Case insensitive
        assert not code.has_prefix("XYZ")

    def test_has_suffix(self):
        """Test has_suffix method."""
        code = ProductCode("ABC-123")

        assert code.has_suffix("123")
        assert not code.has_suffix("456")

    def test_contains(self):
        """Test contains method."""
        code = ProductCode("ABC-123-XYZ")

        assert code.contains("123")
        assert code.contains("abc")  # Case insensitive
        assert not code.contains("456")

    def test_generate_sku(self):
        """Test generate_sku factory method."""
        code = ProductCode.generate_sku("PROD", 123)
        assert code.value == "PROD-123"

        code = ProductCode.generate_sku("SHIRT", 42, "XL")
        assert code.value == "SHIRT-42-XL"

    def test_is_valid_code_static_method(self):
        """Test is_valid_code static method."""
        assert ProductCode.is_valid_code("ABC-123")
        assert not ProductCode.is_valid_code("ABC@123")

    def test_equality_case_insensitive(self):
        """Test that equality is case insensitive."""
        c1 = ProductCode("abc-123")
        c2 = ProductCode("ABC-123")

        assert c1 == c2


class TestPercentage:
    """Tests for Percentage value object."""

    def test_create_valid_percentage(self):
        """Test creating valid percentage."""
        pct = Percentage(Decimal("10"))
        assert pct.value == Decimal("10")

    def test_percentage_from_int(self):
        """Test creating percentage from int."""
        pct = Percentage(10)
        assert pct.value == Decimal("10")

    def test_percentage_above_100_raises_error(self):
        """Test that percentage > 100 raises error."""
        with pytest.raises(ValidationError):
            Percentage(Decimal("150"))

    def test_percentage_below_0_raises_error(self):
        """Test that percentage < 0 raises error."""
        with pytest.raises(ValidationError):
            Percentage(Decimal("-10"))

    def test_as_decimal(self):
        """Test as_decimal method."""
        pct = Percentage(Decimal("10"))
        assert pct.as_decimal() == Decimal("0.1")

        pct = Percentage(Decimal("50"))
        assert pct.as_decimal() == Decimal("0.5")

    def test_of_decimal_amount(self):
        """Test calculating percentage of decimal amount."""
        pct = Percentage(Decimal("10"))
        result = pct.of(Decimal("100"))

        assert result == Decimal("10")

    def test_of_money(self):
        """Test calculating percentage of money."""
        pct = Percentage(Decimal("10"))
        money = Money(Decimal("100"), "USD")
        result = pct.of(money)

        assert result.amount == Decimal("10")
        assert result.currency == "USD"

    def test_add_to_decimal(self):
        """Test add_to with decimal amount."""
        pct = Percentage(Decimal("10"))
        result = pct.add_to(Decimal("100"))

        assert result == Decimal("110")

    def test_add_to_money(self):
        """Test add_to with money."""
        pct = Percentage(Decimal("10"))
        money = Money(Decimal("100"), "USD")
        result = pct.add_to(money)

        assert result.amount == Decimal("110")

    def test_subtract_from_decimal(self):
        """Test subtract_from with decimal amount."""
        pct = Percentage(Decimal("10"))
        result = pct.subtract_from(Decimal("100"))

        assert result == Decimal("90")

    def test_subtract_from_money(self):
        """Test subtract_from with money."""
        pct = Percentage(Decimal("10"))
        money = Money(Decimal("100"), "USD")
        result = pct.subtract_from(money)

        assert result.amount == Decimal("90")

    def test_add_percentages(self):
        """Test adding percentages."""
        p1 = Percentage(Decimal("10"))
        p2 = Percentage(Decimal("5"))
        result = p1.add(p2)

        assert result.value == Decimal("15")

    def test_add_percentages_exceeding_100_raises_error(self):
        """Test that adding percentages > 100 raises error."""
        p1 = Percentage(Decimal("60"))
        p2 = Percentage(Decimal("50"))

        with pytest.raises(ValidationError):
            p1.add(p2)

    def test_subtract_percentages(self):
        """Test subtracting percentages."""
        p1 = Percentage(Decimal("10"))
        p2 = Percentage(Decimal("3"))
        result = p1.subtract(p2)

        assert result.value == Decimal("7")

    def test_multiply(self):
        """Test multiplying percentage by scalar."""
        pct = Percentage(Decimal("10"))
        result = pct.multiply(2)

        assert result.value == Decimal("20")

    def test_is_zero(self):
        """Test is_zero method."""
        assert Percentage.zero().is_zero()
        assert not Percentage(Decimal("1")).is_zero()

    def test_is_full(self):
        """Test is_full method."""
        assert Percentage.full().is_full()
        assert not Percentage(Decimal("50")).is_full()

    def test_comparison_operators(self):
        """Test comparison operators."""
        p1 = Percentage(Decimal("10"))
        p2 = Percentage(Decimal("20"))
        p3 = Percentage(Decimal("10"))

        assert p1 < p2
        assert p1 <= p2
        assert p1 <= p3
        assert p2 > p1
        assert p2 >= p1
        assert p1 >= p3

    def test_str_representation(self):
        """Test string representation."""
        pct = Percentage(Decimal("10"))
        assert str(pct) == "10%"

    def test_from_decimal(self):
        """Test from_decimal factory method."""
        pct = Percentage.from_decimal(Decimal("0.1"))
        assert pct.value == Decimal("10")

    def test_from_ratio(self):
        """Test from_ratio factory method."""
        pct = Percentage.from_ratio(1, 4)
        assert pct.value == Decimal("25")

        pct = Percentage.from_ratio(1, 2)
        assert pct.value == Decimal("50")


class TestValueObjectImmutability:
    """Test immutability of all value objects."""

    def test_money_immutable(self):
        """Test that Money is immutable."""
        money = Money(Decimal("10"), "USD")

        with pytest.raises((AttributeError, FrozenInstanceError)):
            money.amount = Decimal("20")

    def test_email_immutable(self):
        """Test that Email is immutable."""
        email = Email("test@example.com")

        with pytest.raises((AttributeError, FrozenInstanceError)):
            email.value = "other@example.com"

    def test_address_immutable(self):
        """Test that Address is immutable."""
        address = Address(
            street="123 Main St",
            city="Springfield",
            postal_code="62701",
            country="USA",
        )

        with pytest.raises((AttributeError, FrozenInstanceError)):
            address.street = "456 Oak Ave"

    def test_percentage_immutable(self):
        """Test that Percentage is immutable."""
        pct = Percentage(Decimal("10"))

        with pytest.raises((AttributeError, FrozenInstanceError)):
            pct.value = Decimal("20")


class TestValueObjectEquality:
    """Test equality of value objects."""

    def test_money_equality(self):
        """Test Money equality."""
        m1 = Money(Decimal("10"), "USD")
        m2 = Money(Decimal("10"), "USD")
        m3 = Money(Decimal("5"), "USD")

        assert m1 == m2
        assert m1 is not m2  # Different instances
        assert m1 != m3

    def test_email_equality(self):
        """Test Email equality."""
        e1 = Email("test@example.com")
        e2 = Email("TEST@EXAMPLE.COM")  # Normalized
        e3 = Email("other@example.com")

        assert e1 == e2  # Same after normalization
        assert e1 != e3

    def test_product_code_equality(self):
        """Test ProductCode equality."""
        c1 = ProductCode("ABC-123")
        c2 = ProductCode("abc-123")  # Normalized
        c3 = ProductCode("XYZ-789")

        assert c1 == c2  # Same after normalization
        assert c1 != c3


class TestValueObjectHashability:
    """Test that value objects are hashable."""

    def test_money_hashable(self):
        """Test that Money is hashable."""
        m1 = Money(Decimal("10"), "USD")
        m2 = Money(Decimal("10"), "USD")

        # Can use in sets and dicts
        money_set = {m1, m2}
        assert len(money_set) == 1  # Same value

        money_dict = {m1: "value"}
        assert money_dict[m2] == "value"  # Can use as key

    def test_email_hashable(self):
        """Test that Email is hashable."""
        e1 = Email("test@example.com")
        e2 = Email("test@example.com")

        email_set = {e1, e2}
        assert len(email_set) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
