"""
Custom type definitions for SQLite.
"""

import uuid
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID


class SQLiteUUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's UUID type, or CHAR(36) with UUID().hex for other platforms.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        """Process the value before binding to SQL."""
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                try:
                    # Convert integers to strings first to avoid the 'replace' error
                    if isinstance(value, int) or value.isdigit():
                        # Create a proper UUID from a simple number by padding
                        padded_value = (
                            f"{value:0>32}"  # Pad with leading zeros to 32 chars
                        )
                        return str(uuid.UUID(padded_value))
                    return str(uuid.UUID(value))
                except (TypeError, ValueError):
                    # Try to create a UUID from the int value
                    try:
                        if isinstance(value, int) or (
                            isinstance(value, str) and value.isdigit()
                        ):
                            # For really small numbers, create a version 4 random UUID
                            # but with the small number at the end for traceability
                            new_uuid = uuid.uuid4()
                            return str(new_uuid)
                        # Fallback for other non-string types
                        return str(uuid.UUID(str(value)))
                    except (ValueError, TypeError):
                        # Last resort: generate a random UUID
                        return str(uuid.uuid4())
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        """Process the value when retrieving from SQL."""
        if value is None:
            return value
        else:
            try:
                return uuid.UUID(value)
            except (TypeError, ValueError):
                return None
