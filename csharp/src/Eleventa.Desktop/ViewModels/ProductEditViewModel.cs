using ReactiveUI;
using System;
using System.Reactive;
using System.Threading.Tasks;

namespace Eleventa.Desktop.ViewModels;

/// <summary>
/// ViewModel for editing or creating a product.
/// </summary>
public class ProductEditViewModel : ViewModelBase
{
    private readonly IServiceProvider _serviceProvider;
    private Guid _id;
    private string _sku = string.Empty;
    private string _name = string.Empty;
    private string _description = string.Empty;
    private decimal _price;
    private decimal _cost;
    private int _stock;
    private string _barcode = string.Empty;
    private bool _isActive = true;

    public ProductEditViewModel(IServiceProvider serviceProvider, Guid? productId = null)
    {
        _serviceProvider = serviceProvider ?? throw new ArgumentNullException(nameof(serviceProvider));

        SaveCommand = ReactiveCommand.CreateFromTask(Save);
        CancelCommand = ReactiveCommand.Create(Cancel);

        if (productId.HasValue)
        {
            Task.Run(() => LoadProduct(productId.Value));
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

    public string Description
    {
        get => _description;
        set => this.RaiseAndSetIfChanged(ref _description, value);
    }

    public decimal Price
    {
        get => _price;
        set => this.RaiseAndSetIfChanged(ref _price, value);
    }

    public decimal Cost
    {
        get => _cost;
        set => this.RaiseAndSetIfChanged(ref _cost, value);
    }

    public int Stock
    {
        get => _stock;
        set => this.RaiseAndSetIfChanged(ref _stock, value);
    }

    public string Barcode
    {
        get => _barcode;
        set => this.RaiseAndSetIfChanged(ref _barcode, value);
    }

    public bool IsActive
    {
        get => _isActive;
        set => this.RaiseAndSetIfChanged(ref _isActive, value);
    }

    public ReactiveCommand<Unit, Unit> SaveCommand { get; }
    public ReactiveCommand<Unit, Unit> CancelCommand { get; }

    private async Task LoadProduct(Guid productId)
    {
        IsBusy = true;
        try
        {
            // TODO: Load product from service
            // var product = await _productService.GetByIdAsync(productId);
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
            // TODO: Validate and save product
            // await _productService.SaveAsync(product);
            await Task.CompletedTask;
        }
        finally
        {
            IsBusy = false;
        }
    }

    private void Cancel()
    {
        // TODO: Navigate back to product list
    }
}
