using System.Text.RegularExpressions;

namespace Eleventa.Domain.ValueObjects;

/// <summary>
/// Represents an email address.
/// Validates format and provides email operations.
/// </summary>
public sealed class Email : ValueObject
{
    private static readonly Regex EmailRegex = new(
        @"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        RegexOptions.Compiled | RegexOptions.IgnoreCase);

    public string Value { get; }

    private Email(string value)
    {
        Value = value;
    }

    /// <summary>
    /// Creates a new Email instance.
    /// </summary>
    public static Email Create(string email)
    {
        if (string.IsNullOrWhiteSpace(email))
            throw new ValidationException("Email address is required", nameof(email));

        // Normalize to lowercase
        email = email.Trim().ToLowerInvariant();

        if (!EmailRegex.IsMatch(email))
            throw new ValidationException($"Invalid email format: {email}", nameof(email));

        if (email.Length > 254)
            throw new ValidationException("Email address too long (max 254 characters)", nameof(email));

        return new Email(email);
    }

    /// <summary>
    /// Gets the domain part of the email (after @).
    /// </summary>
    public string Domain
    {
        get
        {
            var atIndex = Value.IndexOf('@');
            return atIndex >= 0 ? Value[(atIndex + 1)..] : string.Empty;
        }
    }

    /// <summary>
    /// Gets the local part of the email (before @).
    /// </summary>
    public string LocalPart
    {
        get
        {
            var atIndex = Value.IndexOf('@');
            return atIndex >= 0 ? Value[..atIndex] : Value;
        }
    }

    /// <summary>
    /// Checks if email is from the specified domain.
    /// </summary>
    public bool IsFromDomain(string domain)
    {
        return Domain.Equals(domain, StringComparison.OrdinalIgnoreCase);
    }

    /// <summary>
    /// Returns an obfuscated version of the email for display.
    /// </summary>
    public string Obfuscate()
    {
        var local = LocalPart;
        if (local.Length <= 2)
            return $"*@{Domain}";

        return $"{local[0]}***{local[^1]}@{Domain}";
    }

    protected override IEnumerable<object?> GetEqualityComponents()
    {
        yield return Value;
    }

    public override string ToString() => Value;

    public static implicit operator string(Email email) => email.Value;
}
