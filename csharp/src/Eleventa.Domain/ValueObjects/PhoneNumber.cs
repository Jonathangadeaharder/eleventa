using System.Text.RegularExpressions;

namespace Eleventa.Domain.ValueObjects;

/// <summary>
/// Represents a phone number in E.164 format.
/// </summary>
public sealed class PhoneNumber : ValueObject
{
    private static readonly Regex PhonePattern = new(
        @"^\+[1-9]\d{1,14}$",
        RegexOptions.Compiled);

    public string Value { get; }

    private PhoneNumber(string value)
    {
        Value = value;
    }

    /// <summary>
    /// Creates a new PhoneNumber instance.
    /// </summary>
    public static PhoneNumber Create(string phoneNumber)
    {
        if (string.IsNullOrWhiteSpace(phoneNumber))
            throw new ValidationException("Phone number is required", nameof(phoneNumber));

        // Remove common separators
        var normalized = Regex.Replace(phoneNumber.Trim(), @"[\s\-\(\)\.]", "");

        // Ensure it starts with +
        if (!normalized.StartsWith('+'))
            throw new ValidationException(
                "Phone number must start with + and country code (E.164 format)",
                nameof(phoneNumber));

        if (!PhonePattern.IsMatch(normalized))
            throw new ValidationException(
                "Invalid phone number format (use E.164: +[country][number])",
                nameof(phoneNumber));

        return new PhoneNumber(normalized);
    }

    /// <summary>
    /// Creates a phone number from parts.
    /// </summary>
    public static PhoneNumber FromParts(string countryCode, string areaCode, string number)
    {
        if (string.IsNullOrWhiteSpace(countryCode))
            throw new ArgumentException("Country code is required", nameof(countryCode));

        countryCode = countryCode.TrimStart('+');
        var fullNumber = $"+{countryCode}{areaCode}{number}";

        return Create(fullNumber);
    }

    /// <summary>
    /// Gets the country code.
    /// </summary>
    public string CountryCode
    {
        get
        {
            // Simple heuristic: 1-3 digits after +
            var match = Regex.Match(Value, @"^\+(\d{1,3})");
            return match.Success ? match.Groups[1].Value : string.Empty;
        }
    }

    /// <summary>
    /// Formats the phone number.
    /// </summary>
    public string Format(string format = "international")
    {
        return format.ToLower() switch
        {
            "international" => Value,
            "national" => Value.TrimStart('+'),
            _ => Value
        };
    }

    protected override IEnumerable<object?> GetEqualityComponents()
    {
        yield return Value;
    }

    public override string ToString() => Value;

    public static implicit operator string(PhoneNumber phoneNumber) => phoneNumber.Value;
}
