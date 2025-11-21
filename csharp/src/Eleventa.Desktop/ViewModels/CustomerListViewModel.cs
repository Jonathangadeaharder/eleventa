using ReactiveUI;
using System;
using System.Collections.ObjectModel;
using System.Reactive;
using System.Threading.Tasks;

namespace Eleventa.Desktop.ViewModels;

/// <summary>
/// ViewModel for the Customer List view, displaying all customers with search
/// and CRUD operations.
/// </summary>
public class CustomerListViewModel : ViewModelBase
{
    private readonly IServiceProvider _serviceProvider;
    private string _searchText = string.Empty;
    private CustomerViewModel? _selectedCustomer;

    public CustomerListViewModel(IServiceProvider serviceProvider)
    {
        _serviceProvider = serviceProvider ?? throw new ArgumentNullException(nameof(serviceProvider));

        Customers = new ObservableCollection<CustomerViewModel>();

        AddCustomerCommand = ReactiveCommand.CreateFromTask(AddCustomer);
        EditCustomerCommand = ReactiveCommand.Create(EditCustomer,
            this.WhenAnyValue(x => x.SelectedCustomer, (c) => c != null));
        DeleteCustomerCommand = ReactiveCommand.CreateFromTask(DeleteCustomer,
            this.WhenAnyValue(x => x.SelectedCustomer, (c) => c != null));
        SearchCommand = ReactiveCommand.CreateFromTask(SearchCustomers);

        // Load customers on initialization
        Task.Run(LoadCustomers);
    }

    public ObservableCollection<CustomerViewModel> Customers { get; }

    public string SearchText
    {
        get => _searchText;
        set => this.RaiseAndSetIfChanged(ref _searchText, value);
    }

    public CustomerViewModel? SelectedCustomer
    {
        get => _selectedCustomer;
        set => this.RaiseAndSetIfChanged(ref _selectedCustomer, value);
    }

    public ReactiveCommand<Unit, Unit> AddCustomerCommand { get; }
    public ReactiveCommand<Unit, Unit> EditCustomerCommand { get; }
    public ReactiveCommand<Unit, Unit> DeleteCustomerCommand { get; }
    public ReactiveCommand<Unit, Unit> SearchCommand { get; }

    private async Task LoadCustomers()
    {
        IsBusy = true;
        try
        {
            // TODO: Load customers from service
            Customers.Clear();
            Customers.Add(new CustomerViewModel
            {
                Id = Guid.NewGuid(),
                Name = "Juan Pérez",
                Email = "juan.perez@example.com",
                Phone = "+54 11 1234-5678",
                TaxId = "20-12345678-9"
            });
            Customers.Add(new CustomerViewModel
            {
                Id = Guid.NewGuid(),
                Name = "María González",
                Email = "maria.gonzalez@example.com",
                Phone = "+54 11 8765-4321",
                TaxId = "27-98765432-1"
            });
        }
        finally
        {
            IsBusy = false;
        }
        await Task.CompletedTask;
    }

    private async Task AddCustomer()
    {
        // TODO: Navigate to Customer Edit view with new customer
        await Task.CompletedTask;
    }

    private void EditCustomer()
    {
        if (SelectedCustomer != null)
        {
            // TODO: Navigate to Customer Edit view with selected customer
        }
    }

    private async Task DeleteCustomer()
    {
        if (SelectedCustomer != null)
        {
            // TODO: Show confirmation dialog and delete customer
            Customers.Remove(SelectedCustomer);
        }
        await Task.CompletedTask;
    }

    private async Task SearchCustomers()
    {
        IsBusy = true;
        try
        {
            // TODO: Search customers using search text
            await LoadCustomers();
        }
        finally
        {
            IsBusy = false;
        }
    }
}

/// <summary>
/// ViewModel representation of a Customer for display in the UI.
/// </summary>
public class CustomerViewModel : ViewModelBase
{
    private Guid _id;
    private string _name = string.Empty;
    private string _email = string.Empty;
    private string _phone = string.Empty;
    private string _taxId = string.Empty;
    private string _address = string.Empty;

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
}
