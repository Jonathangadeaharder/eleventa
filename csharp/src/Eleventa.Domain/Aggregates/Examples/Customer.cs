using Eleventa.Domain.ValueObjects;

namespace Eleventa.Domain.Aggregates.Examples;

/// <summary>
/// Customer aggregate root.
/// Manages customer information and addresses.
/// </summary>
public class Customer : AggregateRoot<Guid>
{
    private readonly List<Address> _addresses = new();

    public Email Email { get; private set; }
    public string Name { get; private set; }
    public IReadOnlyCollection<Address> Addresses => _addresses.AsReadOnly();

    public Customer(Guid id, Email email, string name) : base(id)
    {
        if (string.IsNullOrWhiteSpace(name))
            throw new DomainException("Customer name is required");

        Email = email;
        Name = name;
    }

    /// <summary>
    /// Updates customer name.
    /// </summary>
    public void UpdateName(string newName)
    {
        if (string.IsNullOrWhiteSpace(newName))
            throw new DomainException("Customer name is required");

        Name = newName;
    }

    /// <summary>
    /// Updates customer email.
    /// </summary>
    public void UpdateEmail(Email newEmail)
    {
        Email = newEmail;
    }

    /// <summary>
    /// Adds an address to the customer.
    /// </summary>
    public void AddAddress(Address address)
    {
        if (!_addresses.Contains(address))
        {
            _addresses.Add(address);
        }
    }

    /// <summary>
    /// Removes an address from the customer.
    /// </summary>
    public void RemoveAddress(Address address)
    {
        _addresses.Remove(address);
    }

    /// <summary>
    /// Gets the default address (first one).
    /// </summary>
    public Address? GetDefaultAddress()
    {
        return _addresses.FirstOrDefault();
    }
}
