import pytest

from core.exceptions import (
    ApplicationError,
    ValidationError,
    ResourceNotFoundError,
    DatabaseError,
    AuthenticationError,
    BusinessRuleError,
    ExternalServiceError
)

def test_application_error_base():
    """Test raising and catching the base ApplicationError."""
    message = "Base application error"
    with pytest.raises(ApplicationError, match=message) as excinfo:
        raise ApplicationError(message)
    assert excinfo.value.message == message

def test_validation_error():
    """Test raising and catching ValidationError."""
    message = "Invalid input provided"
    with pytest.raises(ValidationError, match=message) as excinfo:
        raise ValidationError(message)
    assert isinstance(excinfo.value, ApplicationError) # Check inheritance
    assert excinfo.value.message == message

def test_resource_not_found_error():
    """Test raising and catching ResourceNotFoundError."""
    message = "Could not find item 123"
    with pytest.raises(ResourceNotFoundError, match=message) as excinfo:
        raise ResourceNotFoundError(message)
    assert isinstance(excinfo.value, ApplicationError)
    assert excinfo.value.message == message

def test_database_error_basic():
    """Test DatabaseError without original exception."""
    message = "DB connection timeout"
    with pytest.raises(DatabaseError, match=message) as excinfo:
        raise DatabaseError(message)
    assert isinstance(excinfo.value, ApplicationError)
    assert excinfo.value.message == message
    assert excinfo.value.original_exception is None

def test_database_error_with_original():
    """Test DatabaseError with an original exception."""
    message = "Constraint violation"
    original_exc = ValueError("Integrity constraint failed")
    with pytest.raises(DatabaseError, match=message) as excinfo:
        raise DatabaseError(message, original_exception=original_exc)
    assert isinstance(excinfo.value, ApplicationError)
    assert excinfo.value.message == message
    assert excinfo.value.original_exception == original_exc

def test_authentication_error():
    """Test raising and catching AuthenticationError."""
    message = "Invalid API key"
    with pytest.raises(AuthenticationError, match=message) as excinfo:
        raise AuthenticationError(message)
    assert isinstance(excinfo.value, ApplicationError)
    assert excinfo.value.message == message

def test_business_rule_error():
    """Test raising and catching BusinessRuleError."""
    message = "Cannot return item after 30 days"
    with pytest.raises(BusinessRuleError, match=message) as excinfo:
        raise BusinessRuleError(message)
    assert isinstance(excinfo.value, ApplicationError)
    assert excinfo.value.message == message

def test_external_service_error_basic():
    """Test ExternalServiceError without service name."""
    message = "Service unavailable"
    with pytest.raises(ExternalServiceError, match=message) as excinfo:
        raise ExternalServiceError(message)
    assert isinstance(excinfo.value, ApplicationError)
    assert excinfo.value.message == message
    assert excinfo.value.service_name is None

def test_external_service_error_with_name():
    """Test ExternalServiceError with a service name."""
    message = "Timeout connecting"
    service = "PaymentGateway"
    # Escape regex special characters like parentheses
    expected_full_message_regex = f"{message} \(Service: {service}\)"
    with pytest.raises(ExternalServiceError, match=expected_full_message_regex) as excinfo:
        raise ExternalServiceError(message, service_name=service)
    assert isinstance(excinfo.value, ApplicationError)
    assert excinfo.value.service_name == service
    # Check the exact message if needed, although match already does
    assert excinfo.value.message == f"{message} (Service: {service})" 