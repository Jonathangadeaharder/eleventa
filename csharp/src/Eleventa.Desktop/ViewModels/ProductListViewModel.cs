using ReactiveUI;
using System;
using System.Collections.ObjectModel;
using System.Reactive;
using System.Threading.Tasks;
using Eleventa.Domain.Entities;

namespace Eleventa.Desktop.ViewModels;

/// <summary>
/// ViewModel for the Product List view, displaying all products with search
/// and CRUD operations.
/// </summary>
public class ProductListViewModel : ViewModelBase
{
    private readonly IServiceProvider _serviceProvider;
    private string _searchText = string.Empty;
    private ProductViewModel? _selectedProduct;

    public ProductListViewModel(IServiceProvider serviceProvider)
    {
        _serviceProvider = serviceProvider ?? throw new ArgumentNullException(nameof(serviceProvider));

        Products = new ObservableCollection<ProductViewModel>();

        AddProductCommand = ReactiveCommand.CreateFromTask(AddProduct);
        EditProductCommand = ReactiveCommand.Create(EditProduct,
            this.WhenAnyValue(x => x.SelectedProduct, (p) => p != null));
        DeleteProductCommand = ReactiveCommand.CreateFromTask(DeleteProduct,
            this.WhenAnyValue(x => x.SelectedProduct, (p) => p != null));
        SearchCommand = ReactiveCommand.CreateFromTask(SearchProducts);

        // Load products on initialization
        Task.Run(LoadProducts);
    }

    public ObservableCollection<ProductViewModel> Products { get; }

    /// <summary>
    /// Gets or sets the search text for filtering products.
    /// </summary>
    public string SearchText
    {
        get => _searchText;
        set => this.RaiseAndSetIfChanged(ref _searchText, value);
    }

    /// <summary>
    /// Gets or sets the currently selected product.
    /// </summary>
    public ProductViewModel? SelectedProduct
    {
        get => _selectedProduct;
        set => this.RaiseAndSetIfChanged(ref _selectedProduct, value);
    }

    public ReactiveCommand<Unit, Unit> AddProductCommand { get; }
    public ReactiveCommand<Unit, Unit> EditProductCommand { get; }
    public ReactiveCommand<Unit, Unit> DeleteProductCommand { get; }
    public ReactiveCommand<Unit, Unit> SearchCommand { get; }

    private async Task LoadProducts()
    {
        IsBusy = true;
        try
        {
            // TODO: Load products from application service
            // var products = await _productService.GetAllAsync();
            // For now, add sample data
            Products.Clear();
            Products.Add(new ProductViewModel
            {
                Id = Guid.NewGuid(),
                Sku = "PROD-001",
                Name = "Sample Product 1",
                Price = 99.99m,
                Stock = 100
            });
            Products.Add(new ProductViewModel
            {
                Id = Guid.NewGuid(),
                Sku = "PROD-002",
                Name = "Sample Product 2",
                Price = 149.99m,
                Stock = 50
            });
        }
        finally
        {
            IsBusy = false;
        }
    }

    private async Task AddProduct()
    {
        // TODO: Navigate to Product Edit view with new product
        await Task.CompletedTask;
    }

    private void EditProduct()
    {
        if (SelectedProduct != null)
        {
            // TODO: Navigate to Product Edit view with selected product
        }
    }

    private async Task DeleteProduct()
    {
        if (SelectedProduct != null)
        {
            // TODO: Show confirmation dialog and delete product
            Products.Remove(SelectedProduct);
        }
        await Task.CompletedTask;
    }

    private async Task SearchProducts()
    {
        IsBusy = true;
        try
        {
            // TODO: Search products using search text
            await LoadProducts();
        }
        finally
        {
            IsBusy = false;
        }
    }
}

/// <summary>
/// ViewModel representation of a Product for display in the UI.
/// </summary>
public class ProductViewModel : ViewModelBase
{
    private Guid _id;
    private string _sku = string.Empty;
    private string _name = string.Empty;
    private decimal _price;
    private int _stock;

    public Guid Id
    {
        get => _id;
        set => this.RaiseAndSetIfChanged(ref _id, value);
    }

    public string Sku
    {
        get => _sku;
        set => this.RaiseAndSetIfChanged(ref _sku, value);
    }

    public string Name
    {
        get => _name;
        set => this.RaiseAndSetIfChanged(ref _name, value);
    }

    public decimal Price
    {
        get => _price;
        set => this.RaiseAndSetIfChanged(ref _price, value);
    }

    public int Stock
    {
        get => _stock;
        set => this.RaiseAndSetIfChanged(ref _stock, value);
    }
}
