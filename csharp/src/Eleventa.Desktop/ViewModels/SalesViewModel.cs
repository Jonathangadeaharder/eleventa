using ReactiveUI;
using System;
using System.Collections.ObjectModel;
using System.Linq;
using System.Reactive;
using System.Threading.Tasks;

namespace Eleventa.Desktop.ViewModels;

/// <summary>
/// ViewModel for the Point of Sale (POS) screen.
/// Handles product selection, cart management, and payment processing.
/// </summary>
public class SalesViewModel : ViewModelBase
{
    private readonly IServiceProvider _serviceProvider;
    private string _searchText = string.Empty;
    private string _customerName = "Walk-in Customer";
    private decimal _total;
    private decimal _subtotal;
    private decimal _tax;
    private decimal _paymentAmount;
    private decimal _change;

    public SalesViewModel(IServiceProvider serviceProvider)
    {
        _serviceProvider = serviceProvider ?? throw new ArgumentNullException(nameof(serviceProvider));

        CartItems = new ObservableCollection<CartItemViewModel>();
        AvailableProducts = new ObservableCollection<ProductViewModel>();

        AddToCartCommand = ReactiveCommand.Create<ProductViewModel>(AddToCart);
        RemoveFromCartCommand = ReactiveCommand.Create<CartItemViewModel>(RemoveFromCart);
        IncreaseQuantityCommand = ReactiveCommand.Create<CartItemViewModel>(IncreaseQuantity);
        DecreaseQuantityCommand = ReactiveCommand.Create<CartItemViewModel>(DecreaseQuantity);
        ProcessPaymentCommand = ReactiveCommand.CreateFromTask(ProcessPayment,
            this.WhenAnyValue(x => x.Total, x => x.PaymentAmount, (t, p) => p >= t && t > 0));
        ClearCartCommand = ReactiveCommand.Create(ClearCart);
        SearchProductsCommand = ReactiveCommand.CreateFromTask(SearchProducts);

        // Load initial products
        Task.Run(LoadProducts);
    }

    public ObservableCollection<CartItemViewModel> CartItems { get; }
    public ObservableCollection<ProductViewModel> AvailableProducts { get; }

    public string SearchText
    {
        get => _searchText;
        set => this.RaiseAndSetIfChanged(ref _searchText, value);
    }

    public string CustomerName
    {
        get => _customerName;
        set => this.RaiseAndSetIfChanged(ref _customerName, value);
    }

    public decimal Total
    {
        get => _total;
        private set => this.RaiseAndSetIfChanged(ref _total, value);
    }

    public decimal Subtotal
    {
        get => _subtotal;
        private set => this.RaiseAndSetIfChanged(ref _subtotal, value);
    }

    public decimal Tax
    {
        get => _tax;
        private set => this.RaiseAndSetIfChanged(ref _tax, value);
    }

    public decimal PaymentAmount
    {
        get => _paymentAmount;
        set
        {
            this.RaiseAndSetIfChanged(ref _paymentAmount, value);
            Change = value - Total;
        }
    }

    public decimal Change
    {
        get => _change;
        private set => this.RaiseAndSetIfChanged(ref _change, value);
    }

    public ReactiveCommand<ProductViewModel, Unit> AddToCartCommand { get; }
    public ReactiveCommand<CartItemViewModel, Unit> RemoveFromCartCommand { get; }
    public ReactiveCommand<CartItemViewModel, Unit> IncreaseQuantityCommand { get; }
    public ReactiveCommand<CartItemViewModel, Unit> DecreaseQuantityCommand { get; }
    public ReactiveCommand<Unit, Unit> ProcessPaymentCommand { get; }
    public ReactiveCommand<Unit, Unit> ClearCartCommand { get; }
    public ReactiveCommand<Unit, Unit> SearchProductsCommand { get; }

    private async Task LoadProducts()
    {
        IsBusy = true;
        try
        {
            // TODO: Load products from service
            AvailableProducts.Clear();
            AvailableProducts.Add(new ProductViewModel
            {
                Id = Guid.NewGuid(),
                Sku = "PROD-001",
                Name = "Sample Product 1",
                Price = 99.99m,
                Stock = 100
            });
            AvailableProducts.Add(new ProductViewModel
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
        await Task.CompletedTask;
    }

    private void AddToCart(ProductViewModel product)
    {
        var existingItem = CartItems.FirstOrDefault(i => i.ProductId == product.Id);
        if (existingItem != null)
        {
            existingItem.Quantity++;
        }
        else
        {
            CartItems.Add(new CartItemViewModel
            {
                ProductId = product.Id,
                ProductName = product.Name,
                UnitPrice = product.Price,
                Quantity = 1
            });
        }
        RecalculateTotal();
    }

    private void RemoveFromCart(CartItemViewModel item)
    {
        CartItems.Remove(item);
        RecalculateTotal();
    }

    private void IncreaseQuantity(CartItemViewModel item)
    {
        item.Quantity++;
        RecalculateTotal();
    }

    private void DecreaseQuantity(CartItemViewModel item)
    {
        if (item.Quantity > 1)
        {
            item.Quantity--;
        }
        else
        {
            CartItems.Remove(item);
        }
        RecalculateTotal();
    }

    private void RecalculateTotal()
    {
        Subtotal = CartItems.Sum(i => i.Total);
        Tax = Subtotal * 0.21m; // 21% tax rate (IVA in Argentina)
        Total = Subtotal + Tax;
        Change = PaymentAmount - Total;
    }

    private async Task ProcessPayment()
    {
        IsBusy = true;
        try
        {
            // TODO: Process payment and create sale
            // await _salesService.CreateSaleAsync(sale);

            // Clear cart after successful payment
            ClearCart();
        }
        finally
        {
            IsBusy = false;
        }
        await Task.CompletedTask;
    }

    private void ClearCart()
    {
        CartItems.Clear();
        PaymentAmount = 0;
        RecalculateTotal();
    }

    private async Task SearchProducts()
    {
        // TODO: Search products by text
        await LoadProducts();
    }
}

/// <summary>
/// ViewModel representation of an item in the shopping cart.
/// </summary>
public class CartItemViewModel : ViewModelBase
{
    private Guid _productId;
    private string _productName = string.Empty;
    private decimal _unitPrice;
    private int _quantity;

    public Guid ProductId
    {
        get => _productId;
        set => this.RaiseAndSetIfChanged(ref _productId, value);
    }

    public string ProductName
    {
        get => _productName;
        set => this.RaiseAndSetIfChanged(ref _productName, value);
    }

    public decimal UnitPrice
    {
        get => _unitPrice;
        set
        {
            this.RaiseAndSetIfChanged(ref _unitPrice, value);
            this.RaisePropertyChanged(nameof(Total));
        }
    }

    public int Quantity
    {
        get => _quantity;
        set
        {
            this.RaiseAndSetIfChanged(ref _quantity, value);
            this.RaisePropertyChanged(nameof(Total));
        }
    }

    public decimal Total => UnitPrice * Quantity;
}
