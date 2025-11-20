using ReactiveUI;
using System;
using System.Reactive;
using System.Threading.Tasks;

namespace Eleventa.Desktop.ViewModels;

/// <summary>
/// ViewModel for editing or creating a customer.
/// </summary>
public class CustomerEditViewModel : ViewModelBase
{
    private readonly IServiceProvider _serviceProvider;
    private Guid _id;
    private string _name = string.Empty;
    private string _email = string.Empty;
    private string _phone = string.Empty;
    private string _taxId = string.Empty;
    private string _address = string.Empty;
    private string _city = string.Empty;
    private string _state = string.Empty;
    private string _postalCode = string.Empty;
    private bool _isActive = true;

    public CustomerEditViewModel(IServiceProvider serviceProvider, Guid? customerId = null)
    {
        _serviceProvider = serviceProvider ?? throw new ArgumentNullException(nameof(serviceProvider));

        SaveCommand = ReactiveCommand.CreateFromTask(Save);
        CancelCommand = ReactiveCommand.Create(Cancel);

        if (customerId.HasValue)
        {
            Task.Run(() => LoadCustomer(customerId.Value));
        }
        else
        {
            _id = Guid.NewGuid();
        }
    }

    public Guid Id
    {
        get => _id;
        set => this.RaiseAndSetIfChanged(ref _id, value);
    }

    public string Name
    {
        get => _name;
        set => this.RaiseAndSetIfChanged(ref _name, value);
    }

    public string Email
    {
        get => _email;
        set => this.RaiseAndSetIfChanged(ref _email, value);
    }

    public string Phone
    {
        get => _phone;
        set => this.RaiseAndSetIfChanged(ref _phone, value);
    }

    public string TaxId
    {
        get => _taxId;
        set => this.RaiseAndSetIfChanged(ref _taxId, value);
    }

    public string Address
    {
        get => _address;
        set => this.RaiseAndSetIfChanged(ref _address, value);
    }

    public string City
    {
        get => _city;
        set => this.RaiseAndSetIfChanged(ref _city, value);
    }

    public string State
    {
        get => _state;
        set => this.RaiseAndSetIfChanged(ref _state, value);
    }

    public string PostalCode
    {
        get => _postalCode;
        set => this.RaiseAndSetIfChanged(ref _postalCode, value);
    }

    public bool IsActive
    {
        get => _isActive;
        set => this.RaiseAndSetIfChanged(ref _isActive, value);
    }

    public ReactiveCommand<Unit, Unit> SaveCommand { get; }
    public ReactiveCommand<Unit, Unit> CancelCommand { get; }

    private async Task LoadCustomer(Guid customerId)
    {
        IsBusy = true;
        try
        {
            // TODO: Load customer from service
            // var customer = await _customerService.GetByIdAsync(customerId);
            await Task.CompletedTask;
        }
        finally
        {
            IsBusy = false;
        }
    }

    private async Task Save()
    {
        IsBusy = true;
        try
        {
            // TODO: Validate and save customer
            // await _customerService.SaveAsync(customer);
            await Task.CompletedTask;
        }
        finally
        {
            IsBusy = false;
        }
    }

    private void Cancel()
    {
        // TODO: Navigate back to customer list
    }
}
