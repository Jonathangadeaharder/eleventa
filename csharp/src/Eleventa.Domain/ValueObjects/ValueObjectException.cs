namespace Eleventa.Domain.ValueObjects;

/// <summary>
/// Base exception for value object errors.
/// </summary>
public class ValueObjectException : Exception
{
    public ValueObjectException(string message) : base(message)
    {
    }

    public ValueObjectException(string message, Exception innerException)
        : base(message, innerException)
    {
    }
}

/// <summary>
/// Exception thrown when value object validation fails.
/// </summary>
public class ValidationException : ValueObjectException
{
    public string? Field { get; }

    public ValidationException(string message, string? field = null)
        : base(message)
    {
        Field = field;
    }
}
