using ReactiveUI;
using System;
using System.Reactive;
using Microsoft.Extensions.DependencyInjection;

namespace Eleventa.Desktop.ViewModels;

/// <summary>
/// Main window ViewModel that handles navigation between different views.
/// </summary>
public class MainWindowViewModel : ViewModelBase
{
    private readonly IServiceProvider _serviceProvider;
    private ViewModelBase _currentView;

    public MainWindowViewModel(IServiceProvider serviceProvider)
    {
        _serviceProvider = serviceProvider ?? throw new ArgumentNullException(nameof(serviceProvider));

        // Initialize with Product List view
        _currentView = new ProductListViewModel(serviceProvider);

        // Setup navigation commands
        ShowProductsCommand = ReactiveCommand.Create(ShowProducts);
        ShowSalesCommand = ReactiveCommand.Create(ShowSales);
        ShowCustomersCommand = ReactiveCommand.Create(ShowCustomers);
        ShowInventoryCommand = ReactiveCommand.Create(ShowInventory);
    }

    /// <summary>
    /// Gets or sets the currently displayed view.
    /// </summary>
    public ViewModelBase CurrentView
    {
        get => _currentView;
        set => this.RaiseAndSetIfChanged(ref _currentView, value);
    }

    public ReactiveCommand<Unit, Unit> ShowProductsCommand { get; }
    public ReactiveCommand<Unit, Unit> ShowSalesCommand { get; }
    public ReactiveCommand<Unit, Unit> ShowCustomersCommand { get; }
    public ReactiveCommand<Unit, Unit> ShowInventoryCommand { get; }

    private void ShowProducts()
    {
        CurrentView = new ProductListViewModel(_serviceProvider);
    }

    private void ShowSales()
    {
        CurrentView = new SalesViewModel(_serviceProvider);
    }

    private void ShowCustomers()
    {
        CurrentView = new CustomerListViewModel(_serviceProvider);
    }

    private void ShowInventory()
    {
        CurrentView = new InventoryViewModel(_serviceProvider);
    }
}
