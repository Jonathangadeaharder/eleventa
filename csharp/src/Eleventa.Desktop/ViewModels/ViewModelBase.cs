using ReactiveUI;

namespace Eleventa.Desktop.ViewModels;

/// <summary>
/// Base class for all ViewModels, providing INotifyPropertyChanged implementation
/// through ReactiveUI.
/// </summary>
public class ViewModelBase : ReactiveObject
{
    private bool _isBusy;

    /// <summary>
    /// Gets or sets a value indicating whether the ViewModel is currently busy
    /// processing an operation.
    /// </summary>
    public bool IsBusy
    {
        get => _isBusy;
        set => this.RaiseAndSetIfChanged(ref _isBusy, value);
    }
}
