# Code Review: TASK-010 - UI: Main Window Shell & Navigation

**Module:** UI  
**Status:** Completed (`[x]`)

## Summary

This task involved creating the main application window (`MainWindow` in `ui/main_window.py`) with a toolbar, status bar, and a `QStackedWidget` for view navigation. The implementation provides the structural foundation for the application's UI.

## Strengths

- **Modular UI Structure:** The use of `QStackedWidget` allows for clean separation of different views (Sales, Products, Inventory, etc.) and easy navigation between them.
- **Service Injection:** The `MainWindow` correctly accepts service instances and the logged-in user via its constructor, making them available to child views.
- **View Management:** Views are instantiated and added to the `QStackedWidget`, with their indices stored for easy switching via the `switch_view` slot.
- **Toolbar Implementation:** A `QToolBar` is created with `QAction`s for each main view. Actions are connected to the `switch_view` slot using lambdas to pass the correct index.
- **Keyboard Shortcuts:** Shortcuts (F1, F2, etc.) are assigned to toolbar actions for efficient navigation.
- **Status Bar:** A `QStatusBar` is implemented, showing basic status messages and displaying the currently logged-in user.
- **Placeholder Widgets:** Using `PlaceholderWidget` for unimplemented views is a good strategy during development.
- **Isolated Testing:** The `if __name__ == '__main__':` block allows running the `MainWindow` with mock services for UI testing without needing the full application stack.

## Issues / Concerns

- **Hardcoded View Names/Indices:** Using dictionaries (`self.views`, `self.view_indices`) with string keys is functional but could be slightly more robust using enums or constants, especially if view names change.
- **Error Handling:** The `switch_view` method prints an error for invalid indices but doesn't provide user feedback.
- **Icon Integration:** Toolbar actions currently lack icons, which would improve visual appeal and usability.

## Suggestions

- **Use Enums for Views:** Consider using an `Enum` to represent the different views and their indices for better type safety and maintainability.
- **Add Icons:** Integrate icons into the `QAction`s on the toolbar.
- **User Feedback for Errors:** Show a message box or status bar update if an invalid view index is somehow requested in `switch_view`.
- **Refactor View Instantiation:** If the number of views and services grows significantly, consider a more structured approach to view creation and service injection, perhaps using a factory or dependency injection container.

## Conclusion

The `MainWindow` implementation provides a solid, extensible, and well-structured foundation for the application's UI. It correctly handles view management, navigation, service injection, and basic status display. Addressing the minor concerns regarding view indexing and adding icons will further enhance its quality. The inclusion of an isolated run block is a good practice for UI development.
