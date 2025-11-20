namespace Eleventa.Domain.ValueObjects;

/// <summary>
/// Represents a physical address.
/// </summary>
public sealed class Address : ValueObject
{
    public string Street { get; }
    public string City { get; }
    public string PostalCode { get; }
    public string Country { get; }
    public string? State { get; }
    public string? AdditionalInfo { get; }

    private Address(
        string street,
        string city,
        string postalCode,
        string country,
        string? state = null,
        string? additionalInfo = null)
    {
        Street = street;
        City = city;
        PostalCode = postalCode;
        Country = country;
        State = state;
        AdditionalInfo = additionalInfo;
    }

    /// <summary>
    /// Creates a new Address instance.
    /// </summary>
    public static Address Create(
        string street,
        string city,
        string postalCode,
        string country,
        string? state = null,
        string? additionalInfo = null)
    {
        if (string.IsNullOrWhiteSpace(street))
            throw new ValidationException("Street is required", nameof(street));

        if (string.IsNullOrWhiteSpace(city))
            throw new ValidationException("City is required", nameof(city));

        if (string.IsNullOrWhiteSpace(postalCode))
            throw new ValidationException("Postal code is required", nameof(postalCode));

        if (string.IsNullOrWhiteSpace(country))
            throw new ValidationException("Country is required", nameof(country));

        return new Address(
            street.Trim(),
            city.Trim(),
            postalCode.Trim(),
            country.Trim(),
            state?.Trim(),
            additionalInfo?.Trim());
    }

    /// <summary>
    /// Checks if address is in the specified country.
    /// </summary>
    public bool IsInCountry(string country)
    {
        return Country.Equals(country, StringComparison.OrdinalIgnoreCase);
    }

    /// <summary>
    /// Returns a single-line representation.
    /// </summary>
    public string ToSingleLine()
    {
        var parts = new List<string> { Street, City };

        if (!string.IsNullOrWhiteSpace(State))
            parts.Add(State);

        parts.Add(PostalCode);
        parts.Add(Country);

        return string.Join(", ", parts);
    }

    /// <summary>
    /// Returns a multi-line representation.
    /// </summary>
    public string ToMultiLine()
    {
        var lines = new List<string> { Street };

        if (!string.IsNullOrWhiteSpace(AdditionalInfo))
            lines.Add(AdditionalInfo);

        var cityLine = City;
        if (!string.IsNullOrWhiteSpace(State))
            cityLine += $", {State}";
        cityLine += $" {PostalCode}";

        lines.Add(cityLine);
        lines.Add(Country);

        return string.Join(Environment.NewLine, lines);
    }

    protected override IEnumerable<object?> GetEqualityComponents()
    {
        yield return Street;
        yield return City;
        yield return PostalCode;
        yield return Country;
        yield return State;
        yield return AdditionalInfo;
    }

    public override string ToString() => ToSingleLine();
}
