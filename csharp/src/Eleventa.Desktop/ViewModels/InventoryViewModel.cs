using ReactiveUI;
using System;
using System.Collections.ObjectModel;
using System.Reactive;
using System.Threading.Tasks;

namespace Eleventa.Desktop.ViewModels;

/// <summary>
/// ViewModel for the Inventory view, displaying stock levels and movements.
/// </summary>
public class InventoryViewModel : ViewModelBase
{
    private readonly IServiceProvider _serviceProvider;
    private string _searchText = string.Empty;
    private InventoryItemViewModel? _selectedItem;

    public InventoryViewModel(IServiceProvider serviceProvider)
    {
        _serviceProvider = serviceProvider ?? throw new ArgumentNullException(nameof(serviceProvider));

        InventoryItems = new ObservableCollection<InventoryItemViewModel>();

        AdjustStockCommand = ReactiveCommand.CreateFromTask(AdjustStock,
            this.WhenAnyValue(x => x.SelectedItem, (i) => i != null));
        SearchCommand = ReactiveCommand.CreateFromTask(SearchInventory);
        RefreshCommand = ReactiveCommand.CreateFromTask(LoadInventory);

        // Load inventory on initialization
        Task.Run(LoadInventory);
    }

    public ObservableCollection<InventoryItemViewModel> InventoryItems { get; }

    public string SearchText
    {
        get => _searchText;
        set => this.RaiseAndSetIfChanged(ref _searchText, value);
    }

    public InventoryItemViewModel? SelectedItem
    {
        get => _selectedItem;
        set => this.RaiseAndSetIfChanged(ref _selectedItem, value);
    }

    public ReactiveCommand<Unit, Unit> AdjustStockCommand { get; }
    public ReactiveCommand<Unit, Unit> SearchCommand { get; }
    public ReactiveCommand<Unit, Unit> RefreshCommand { get; }

    private async Task LoadInventory()
    {
        IsBusy = true;
        try
        {
            // TODO: Load inventory from service
            InventoryItems.Clear();
            InventoryItems.Add(new InventoryItemViewModel
            {
                ProductId = Guid.NewGuid(),
                Sku = "PROD-001",
                ProductName = "Sample Product 1",
                CurrentStock = 100,
                MinimumStock = 20,
                MaximumStock = 200,
                Status = "OK"
            });
            InventoryItems.Add(new InventoryItemViewModel
            {
                ProductId = Guid.NewGuid(),
                Sku = "PROD-002",
                ProductName = "Sample Product 2",
                CurrentStock = 15,
                MinimumStock = 20,
                MaximumStock = 150,
                Status = "Low Stock"
            });
            InventoryItems.Add(new InventoryItemViewModel
            {
                ProductId = Guid.NewGuid(),
                Sku = "PROD-003",
                ProductName = "Sample Product 3",
                CurrentStock = 0,
                MinimumStock = 10,
                MaximumStock = 100,
                Status = "Out of Stock"
            });
        }
        finally
        {
            IsBusy = false;
        }
        await Task.CompletedTask;
    }

    private async Task AdjustStock()
    {
        if (SelectedItem != null)
        {
            // TODO: Show stock adjustment dialog
        }
        await Task.CompletedTask;
    }

    private async Task SearchInventory()
    {
        IsBusy = true;
        try
        {
            // TODO: Search inventory using search text
            await LoadInventory();
        }
        finally
        {
            IsBusy = false;
        }
    }
}

/// <summary>
/// ViewModel representation of an Inventory item for display in the UI.
/// </summary>
public class InventoryItemViewModel : ViewModelBase
{
    private Guid _productId;
    private string _sku = string.Empty;
    private string _productName = string.Empty;
    private int _currentStock;
    private int _minimumStock;
    private int _maximumStock;
    private string _status = string.Empty;

    public Guid ProductId
    {
        get => _productId;
        set => this.RaiseAndSetIfChanged(ref _productId, value);
    }

    public string Sku
    {
        get => _sku;
        set => this.RaiseAndSetIfChanged(ref _sku, value);
    }

    public string ProductName
    {
        get => _productName;
        set => this.RaiseAndSetIfChanged(ref _productName, value);
    }

    public int CurrentStock
    {
        get => _currentStock;
        set => this.RaiseAndSetIfChanged(ref _currentStock, value);
    }

    public int MinimumStock
    {
        get => _minimumStock;
        set => this.RaiseAndSetIfChanged(ref _minimumStock, value);
    }

    public int MaximumStock
    {
        get => _maximumStock;
        set => this.RaiseAndSetIfChanged(ref _maximumStock, value);
    }

    public string Status
    {
        get => _status;
        set => this.RaiseAndSetIfChanged(ref _status, value);
    }
}
