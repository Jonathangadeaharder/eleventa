"""
TaxId Value Object

Represents a tax identification number (CUIT in Argentina).

CUIT (Código Único de Identificación Tributaria) is Argentina's tax ID.
Format: XX-XXXXXXXX-X (11 digits with check digit)

Usage:
    # Create with validation
    cuit = TaxId('20-12345678-9')

    # Validation happens automatically
    try:
        invalid = TaxId('12-34567')  # Raises ValidationError
    except ValidationError as e:
        print(e.message)

    # Formatting
    print(cuit.format())  # '20-12345678-9'
    print(cuit.digits)    # '20123456789'
"""

from dataclasses import dataclass
import re
from core.value_objects.base import ValueObject, ValidationError, validate_not_empty


@dataclass(frozen=True)
class TaxId(ValueObject):
    """
    Represents a tax identification number (CUIT).

    CUIT format: XX-XXXXXXXX-X (11 digits total)
    - First 2 digits: Type (20=person, 23=company, 27=person-monotributista, etc.)
    - Next 8 digits: DNI or sequence number
    - Last digit: Verification digit

    Attributes:
        value: The normalized tax ID (digits only)

    Raises:
        ValidationError: If tax ID format is invalid

    Examples:
        >>> cuit = TaxId('20-12345678-9')
        >>> str(cuit)
        '20-12345678-9'

        >>> cuit.digits
        '20123456789'

        >>> cuit.type_code
        '20'
    """

    value: str

    # CUIT pattern: accepts XX-XXXXXXXX-X or XXXXXXXXXXX
    CUIT_PATTERN = re.compile(r"^\d{2}-?\d{8}-?\d{1}$")

    def __post_init__(self):
        """Validate tax ID on creation."""
        # Check not empty
        validate_not_empty(self.value, "Tax ID")

        # Remove whitespace and dashes for validation
        test_value = self.value.strip().replace("-", "")

        # Check format
        if not re.match(r"^\d{11}$", test_value):
            raise ValidationError(
                f"Tax ID must be 11 digits (got '{self.value}')", field="tax_id"
            )

        # Validate check digit
        if not self._validate_check_digit(test_value):
            raise ValidationError(
                f"Invalid tax ID check digit: '{self.value}'", field="tax_id"
            )

        # Store normalized (digits only)
        object.__setattr__(self, "value", test_value)

    @staticmethod
    def _validate_check_digit(cuit: str) -> bool:
        """
        Validate CUIT check digit using official algorithm.

        Args:
            cuit: CUIT as 11 digits

        Returns:
            True if check digit is valid
        """
        if len(cuit) != 11:
            return False

        # CUIT validation multipliers
        multipliers = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]

        # Calculate sum
        total = sum(int(cuit[i]) * multipliers[i] for i in range(10))

        # Calculate check digit
        remainder = total % 11
        check_digit = 11 - remainder

        if check_digit == 11:
            check_digit = 0
        elif check_digit == 10:
            check_digit = 9

        # Compare with provided check digit
        return int(cuit[10]) == check_digit

    @property
    def digits(self) -> str:
        """
        Get tax ID as digits only.

        Returns:
            Tax ID digits

        Examples:
            >>> TaxId('20-12345678-9').digits
            '20123456789'
        """
        return self.value

    @property
    def type_code(self) -> str:
        """
        Get the type code (first 2 digits).

        Type codes:
        - 20: Male individual
        - 23: Company
        - 24: Foreign person
        - 27: Female individual
        - 30: Public entity
        - 33: Joint venture
        - 34: Foreign company

        Returns:
            Type code

        Examples:
            >>> TaxId('20-12345678-9').type_code
            '20'
        """
        return self.value[:2]

    @property
    def document_number(self) -> str:
        """
        Get the document number (middle 8 digits).

        Returns:
            Document number

        Examples:
            >>> TaxId('20-12345678-9').document_number
            '12345678'
        """
        return self.value[2:10]

    @property
    def check_digit(self) -> str:
        """
        Get the check digit (last digit).

        Returns:
            Check digit

        Examples:
            >>> TaxId('20-12345678-9').check_digit
            '9'
        """
        return self.value[10]

    def format(self, separator: str = "-") -> str:
        """
        Format tax ID with separators.

        Args:
            separator: Separator to use (default: '-')

        Returns:
            Formatted tax ID

        Examples:
            >>> cuit = TaxId('20123456789')
            >>> cuit.format()
            '20-12345678-9'

            >>> cuit.format('/')
            '20/12345678/9'
        """
        return f"{self.type_code}{separator}{self.document_number}{separator}{self.check_digit}"

    def is_person(self) -> bool:
        """
        Check if tax ID belongs to an individual.

        Returns:
            True if individual

        Examples:
            >>> TaxId('20-12345678-9').is_person()
            True
            >>> TaxId('23-12345678-9').is_person()
            False
        """
        return self.type_code in ("20", "23", "24", "27")

    def is_company(self) -> bool:
        """
        Check if tax ID belongs to a company.

        Returns:
            True if company

        Examples:
            >>> TaxId('30-12345678-9').is_company()
            True
            >>> TaxId('20-12345678-9').is_company()
            False
        """
        return self.type_code in ("30", "33", "34")

    def __str__(self) -> str:
        """
        String representation (formatted).

        Returns:
            Formatted tax ID

        Examples:
            >>> str(TaxId('20123456789'))
            '20-12345678-9'
        """
        return self.format()

    def __repr__(self) -> str:
        """
        Developer-friendly representation.

        Returns:
            TaxId representation

        Examples:
            >>> TaxId('20123456789')
            TaxId('20-12345678-9')
        """
        return f"TaxId('{self.format()}')"

    @classmethod
    def from_dni(cls, dni: str, gender: str = "M") -> "TaxId":
        """
        Create CUIT from DNI (Documento Nacional de Identidad).

        Args:
            dni: DNI number (8 digits)
            gender: 'M' for male, 'F' for female (default: 'M')

        Returns:
            TaxId instance

        Examples:
            >>> cuit = TaxId.from_dni('12345678', 'M')
            >>> cuit.type_code
            '20'
        """
        # Validate DNI
        dni = dni.strip()
        if not re.match(r"^\d{7,8}$", dni):
            raise ValidationError(f"Invalid DNI format: '{dni}'")

        # Pad to 8 digits if needed
        dni = dni.zfill(8)

        # Determine type code based on gender
        type_code = "20" if gender.upper() == "M" else "27"

        # Calculate check digit
        temp_cuit = type_code + dni

        # Use multipliers
        multipliers = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        total = sum(int(temp_cuit[i]) * multipliers[i] for i in range(10))

        remainder = total % 11
        check_digit = 11 - remainder

        if check_digit == 11:
            check_digit = 0
        elif check_digit == 10:
            check_digit = 9

        full_cuit = temp_cuit + str(check_digit)
        return cls(full_cuit)

    @classmethod
    def is_valid_cuit(cls, cuit: str) -> bool:
        """
        Check if string is a valid CUIT without raising exception.

        Args:
            cuit: String to validate

        Returns:
            True if valid CUIT

        Examples:
            >>> TaxId.is_valid_cuit('20-12345678-9')
            True  # if check digit is valid
            >>> TaxId.is_valid_cuit('invalid')
            False
        """
        try:
            cls(cuit)
            return True
        except ValidationError:
            return False
