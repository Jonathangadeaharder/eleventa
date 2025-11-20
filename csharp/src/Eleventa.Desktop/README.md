# Eleventa.Desktop - Avalonia MVVM Application

A modern, cross-platform desktop application for the Eleventa POS system built with Avalonia UI and the MVVM pattern.

## Architecture

This application follows the **Model-View-ViewModel (MVVM)** pattern and uses **ReactiveUI** for property change notifications and command handling.

### Project Structure

```
Eleventa.Desktop/
├── Program.cs                      # Application entry point
├── App.axaml                       # Application-level XAML with styles
├── App.axaml.cs                    # Application code-behind
├── MainWindow.axaml                # Main window with navigation
├── MainWindow.axaml.cs             # Main window code-behind
├── Assets/                         # Images, icons, and other resources
├── Services/
│   └── ServiceCollectionExtensions.cs  # DI container configuration
├── ViewModels/                     # All ViewModels
│   ├── ViewModelBase.cs           # Base ViewModel with INotifyPropertyChanged
│   ├── MainWindowViewModel.cs     # Main window with navigation
│   ├── ProductListViewModel.cs    # Product list and search
│   ├── ProductEditViewModel.cs    # Product create/edit
│   ├── SalesViewModel.cs          # POS/Sales screen
│   ├── CustomerListViewModel.cs   # Customer list and search
│   ├── CustomerEditViewModel.cs   # Customer create/edit
│   └── InventoryViewModel.cs      # Inventory management
└── Views/                         # All XAML Views
    ├── ProductListView.axaml
    ├── ProductEditView.axaml
    ├── SalesView.axaml
    ├── CustomerListView.axaml
    ├── CustomerEditView.axaml
    └── InventoryView.axaml
```

## Features

### 1. Navigation System
- Top navigation bar with buttons for each major section
- Content area that dynamically displays the selected view
- Implemented in `MainWindow.axaml` using `ContentControl` with `DataTemplates`

### 2. Product Management
- **ProductListView**: Browse all products, search, add/edit/delete
- **ProductEditView**: Create or edit product details (SKU, name, price, cost, stock, barcode)
- Features:
  - DataGrid with sortable columns
  - Search functionality
  - CRUD operations

### 3. Point of Sale (POS)
- **SalesView**: Complete POS interface
- Features:
  - Product search and selection
  - Shopping cart with quantity adjustment
  - Real-time total calculation
  - Tax calculation (21% IVA for Argentina)
  - Payment processing with change calculation
  - Customer selection

### 4. Customer Management
- **CustomerListView**: Browse all customers, search, add/edit/delete
- **CustomerEditView**: Create or edit customer details
- Features:
  - Full customer information (name, email, phone, tax ID, address)
  - DataGrid with search
  - CRUD operations

### 5. Inventory Management
- **InventoryView**: Monitor stock levels
- Features:
  - Stock level monitoring
  - Low stock and out-of-stock alerts
  - Stock adjustment functionality
  - Summary cards showing totals

## Technology Stack

- **Avalonia 11.0.10**: Cross-platform UI framework
- **ReactiveUI**: MVVM framework for property change notifications
- **.NET 8.0**: Target framework
- **Microsoft.Extensions.DependencyInjection**: Dependency injection
- **Microsoft.Extensions.Hosting**: Application hosting

## MVVM Pattern Implementation

### ViewModelBase
All ViewModels inherit from `ViewModelBase`, which:
- Inherits from `ReactiveUI.ReactiveObject`
- Provides `INotifyPropertyChanged` implementation
- Includes common properties like `IsBusy` for loading states

### Data Binding
- All properties use `RaiseAndSetIfChanged` for automatic UI updates
- Commands are implemented using `ReactiveCommand`
- Views are bound to ViewModels using `x:DataType` for compile-time checking

### Example ViewModel Property
```csharp
private string _name = string.Empty;

public string Name
{
    get => _name;
    set => this.RaiseAndSetIfChanged(ref _name, value);
}
```

### Example Command
```csharp
public ReactiveCommand<Unit, Unit> SaveCommand { get; }

public MyViewModel()
{
    SaveCommand = ReactiveCommand.CreateFromTask(Save);
}

private async Task Save()
{
    // Implementation
}
```

## Styling

The application uses Fluent Design with custom styles defined in `App.axaml`:

- **Primary Button**: Blue background (#0078D4)
- **Secondary Button**: Gray background (#6C757D)
- **Danger Button**: Red background (#DC3545)
- **Card Style**: White background with border and rounded corners
- **Header/Subheader**: Typography styles for consistent headings

## Dependency Injection

Services are registered in `ServiceCollectionExtensions.cs`:

```csharp
services.AddEleventa();
```

This method will register:
- Domain services and repositories
- Application services
- Infrastructure services (DbContext, etc.)

## Running the Application

### Prerequisites
- .NET 8.0 SDK or later
- Visual Studio 2022, Rider, or VS Code with C# extension

### Build and Run
```bash
# Navigate to the Desktop project
cd csharp/src/Eleventa.Desktop

# Restore packages (if network is available)
dotnet restore

# Build the project
dotnet build

# Run the application
dotnet run
```

### Without Network Access
If package restoration fails due to network issues, the project is still structured correctly. You can:
1. Copy the project to a machine with internet access
2. Run `dotnet restore` there
3. Copy back the restored packages

## Integration with Other Layers

The Desktop application integrates with:

1. **Eleventa.Domain**: Core business entities and domain logic
2. **Eleventa.Application**: Application services and use cases
3. **Eleventa.Infrastructure**: Data persistence and external services

### Next Steps for Integration

1. Implement repository interfaces in Infrastructure layer
2. Implement application services in Application layer
3. Update ViewModels to use injected services instead of sample data
4. Add navigation service for view transitions
5. Add dialog service for confirmations and alerts
6. Implement validation using FluentValidation or similar

## Sample Data

Currently, all ViewModels use sample/mock data for demonstration. Look for `TODO:` comments in the code to find places where real service integration is needed.

## Known Limitations

1. **Navigation**: Currently uses simple view replacement. Consider implementing a navigation service for more complex scenarios.
2. **Validation**: Not yet implemented. Add validation before saving entities.
3. **Error Handling**: Basic error handling. Add comprehensive error handling and user feedback.
4. **Loading States**: `IsBusy` property exists but needs UI indicators in all views.
5. **Icons**: Placeholder for `avalonia-logo.ico` - add actual application icon.

## Future Enhancements

1. Add dialogs for confirmations (delete operations, etc.)
2. Implement print functionality for receipts
3. Add reporting views (sales reports, inventory reports, etc.)
4. Implement user authentication and authorization
5. Add settings/configuration view
6. Implement barcode scanner integration
7. Add multi-language support (i18n)
8. Implement theme switching (light/dark mode)

## Contributing

When adding new views:

1. Create the ViewModel in `ViewModels/` folder
2. Create the View (XAML + code-behind) in `Views/` folder
3. Add navigation command to `MainWindowViewModel` if needed
4. Add DataTemplate to `MainWindow.axaml` for automatic view resolution
5. Follow MVVM pattern strictly - no business logic in code-behind

## License

This project is part of the Eleventa POS system.
