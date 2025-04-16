import sys
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QLineEdit, QPushButton,
    QMessageBox, QApplication, QListWidgetItem, QLabel, QDialogButtonBox
)
from PySide6.QtCore import Qt, Slot
from typing import Optional

# Import Department model
from core.models.product import Department

# Assuming ProductService provides department methods
# from core.services.product_service import ProductService
# For testing, let's create a mock service and department structure
from dataclasses import dataclass

class MockProductService_Departments:
    def __init__(self):
        # Use the imported Department class from core.models.product
        self._departments = [
            Department(id=1, name="Depto A"),
            Department(id=2, name="Bebidas"),
            Department(id=3, name="Limpieza"),
        ]
        self._next_id = 4

    def get_all_departments(self) -> list[Department]:
        print("[MockService] Getting all departments")
        return sorted(self._departments, key=lambda d: d.name)

    def add_department(self, department_data: Department) -> Department:
        print(f"[MockService] Adding department: {department_data.name}")
        if not department_data.name:
            raise ValueError("El nombre del departamento no puede estar vacío.")
        # Check for duplicates (case-insensitive)
        if any(d.name.lower() == department_data.name.lower() for d in self._departments):
            raise ValueError(f"El departamento '{department_data.name}' ya existe.")
        # Assign an ID if not provided
        if department_data.id is None:
            department_data.id = self._next_id
            self._next_id += 1
        self._departments.append(department_data)
        return department_data

    def update_department(self, department_data: Department) -> Department:
        print(f"[MockService] Updating department ID {department_data.id} to: {department_data.name}")
        if not department_data.name:
            raise ValueError("El nombre del departamento no puede estar vacío.")
        if department_data.id is None:
            raise ValueError("Department ID must be provided for update.")
            
        # Check for duplicates excluding self (case-insensitive)
        if any(d.name.lower() == department_data.name.lower() and d.id != department_data.id for d in self._departments):
            raise ValueError(f"Ya existe otro departamento con el nombre '{department_data.name}'.")

        for i, dept in enumerate(self._departments):
            if dept.id == department_data.id:
                self._departments[i] = department_data
                return department_data
        raise ValueError("No se encontró el departamento a actualizar.")

    def delete_department(self, department_id: int):
        print(f"[MockService] Deleting department ID: {department_id}")
        # Check if department exists
        original_length = len(self._departments)
        self._departments = [d for d in self._departments if d.id != department_id]
        if len(self._departments) == original_length:
             raise ValueError("No se encontró el departamento a eliminar.")
        # In a real app, check if the department is in use by products
        # if self.product_repository.exists_product_with_department(department_id):
        #     raise ValueError("No se puede eliminar el departamento porque está asignado a uno o más productos.")


class DepartmentDialog(QDialog):
    """Dialog for managing departments."""

    def __init__(self, product_service, parent=None):
        super().__init__(parent)
        self.product_service = product_service
        self.setWindowTitle("Administrar Departamentos")
        self.setMinimumWidth(450)

        self._current_department_id: Optional[int] = None # Store ID of selected department for editing

        self._init_ui()
        self._connect_signals()
        self._load_departments()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)

        # Left side: List
        list_layout = QVBoxLayout()
        list_layout.addWidget(QLabel("Departamentos Existentes:"))
        self.dept_list_widget = QListWidget()
        self.dept_list_widget.setAlternatingRowColors(True)
        list_layout.addWidget(self.dept_list_widget)
        main_layout.addLayout(list_layout, 2) # Give list more stretch factor

        # Right side: Form and buttons
        form_layout = QVBoxLayout()
        form_layout.addWidget(QLabel("Nombre Departamento:"))
        self.name_input = QLineEdit()
        form_layout.addWidget(self.name_input)
        form_layout.addStretch() # Push buttons down

        self.new_button = QPushButton("Nuevo")
        self.save_button = QPushButton("Guardar")
        self.delete_button = QPushButton("Eliminar")
        self.save_button.setEnabled(False) # Disabled until changes are made or new is clicked
        self.delete_button.setEnabled(False) # Disabled until an item is selected

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.new_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.delete_button)
        form_layout.addLayout(button_layout)

        # Standard buttons (OK/Cancel or just Close)
        # Using Close only as actions are immediate
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        form_layout.addWidget(self.button_box)

        main_layout.addLayout(form_layout, 1)

    def _connect_signals(self):
        self.dept_list_widget.currentItemChanged.connect(self._on_selection_changed)
        self.name_input.textChanged.connect(self._on_name_input_changed)
        self.new_button.clicked.connect(self._new_department)
        self.save_button.clicked.connect(self._save_department)
        self.delete_button.clicked.connect(self._delete_department)
        self.button_box.rejected.connect(self.reject) # Close button action

    @Slot()
    def _load_departments(self):
        """Fetches departments and populates the list widget."""
        self.dept_list_widget.clear()
        try:
            print("Loading departments...")
            departments = self.product_service.get_all_departments()
            print(f"Loaded {len(departments)} departments")
            for dept in departments:
                print(f"Adding department to list: ID={dept.id}, Name={dept.name}, Type={type(dept)}")
                item = QListWidgetItem(dept.name)
                item.setData(Qt.ItemDataRole.UserRole, dept) # Store the whole object
                self.dept_list_widget.addItem(item)
            self._update_button_states()
        except Exception as e:
            print(f"ERROR loading departments: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los departamentos: {e}")


    @Slot(QListWidgetItem, QListWidgetItem)
    def _on_selection_changed(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]):
        """Updates the form when list selection changes."""
        if current:
            department: Department = current.data(Qt.ItemDataRole.UserRole)
            self._current_department_id = department.id
            # Temporarily disconnect signal to avoid loop
            self.name_input.textChanged.disconnect(self._on_name_input_changed)
            self.name_input.setText(department.name)
            self.name_input.textChanged.connect(self._on_name_input_changed)
            self.name_input.setReadOnly(False)
            self.name_input.setFocus() # Ready to edit
        else:
            self._current_department_id = None
            # Keep disconnected when clearing
            self.name_input.textChanged.disconnect(self._on_name_input_changed)
            self.name_input.clear()
            self.name_input.textChanged.connect(self._on_name_input_changed)
            self.name_input.setReadOnly(True) # Can't edit if nothing selected

        self._update_button_states()

    @Slot(str)
    def _on_name_input_changed(self, text: str):
        """Enables save button if text is changed and valid."""
        self._update_button_states()

    def _update_button_states(self):
        """Updates the enabled state of buttons based on selection and input."""
        selected_item = self.dept_list_widget.currentItem()
        is_editing_existing = selected_item is not None and self._current_department_id is not None
        has_text = bool(self.name_input.text().strip())

        self.delete_button.setEnabled(is_editing_existing)

        # Enable Save if:
        # 1. Creating new (no item selected, but New button was clicked - indicated by _current_department_id being None AND name_input not read-only) and has text
        # 2. Editing existing AND text has changed from original AND has text
        original_name = ""
        if is_editing_existing:
            original_name = selected_item.data(Qt.ItemDataRole.UserRole).name

        is_new_mode = self._current_department_id is None and not self.name_input.isReadOnly()
        text_changed = self.name_input.text() != original_name

        can_save = (is_new_mode and has_text) or (is_editing_existing and has_text and text_changed)
        self.save_button.setEnabled(can_save)


    @Slot()
    def _new_department(self):
        """Clears the selection and form to add a new department."""
        self.dept_list_widget.clearSelection()
        self._current_department_id = None # Explicitly mark as new
        self.name_input.clear()
        self.name_input.setReadOnly(False)
        self.name_input.setFocus()
        self._update_button_states()

    @Slot()
    def _save_department(self):
        """Saves a new or updated department."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Entrada Inválida", "El nombre del departamento no puede estar vacío.")
            return

        try:
            if self._current_department_id is None: # Adding new
                # Create a Department object with None as id (will be assigned by the database)
                # This is critical - if we provide an id when it should be auto-generated, it can cause issues
                new_dept_data = Department(id=None, name=name)
                print(f"Creating new department with name: {name}, type: {type(new_dept_data)}")
                new_dept = self.product_service.add_department(new_dept_data)
                print(f"Department created successfully: {new_dept.id}:{new_dept.name}")
                self._load_departments() # Reload to show the new one
                # Optionally select the newly added item
                for i in range(self.dept_list_widget.count()):
                     item = self.dept_list_widget.item(i)
                     if item.data(Qt.ItemDataRole.UserRole).id == new_dept.id:
                         self.dept_list_widget.setCurrentItem(item)
                         break
                QMessageBox.information(self, "Departamento Agregado", f"Departamento '{new_dept.name}' agregado correctamente.")

            else: # Updating existing
                # Create a Department object with ID for updating
                updated_dept_data = Department(id=self._current_department_id, name=name)
                print(f"Updating department {self._current_department_id} to name: {name}")
                # Call update_department with just the Department object
                updated_dept = self.product_service.update_department(updated_dept_data)
                
                # Handle the case where update_department might return None
                if updated_dept is None:
                    print("Warning: update_department returned None")
                    updated_dept = updated_dept_data  # Use the input data as a fallback
                
                print(f"Department updated successfully: {updated_dept.id}:{updated_dept.name}")
                # Update the item text directly instead of full reload if preferred
                selected_item = self.dept_list_widget.currentItem()
                if selected_item and selected_item.data(Qt.ItemDataRole.UserRole).id == updated_dept.id:
                    selected_item.setText(updated_dept.name)
                    selected_item.setData(Qt.ItemDataRole.UserRole, updated_dept) # Update stored data too
                    self._update_button_states() # Reset save button state
                else: # Fallback if selection somehow got lost
                    self._load_departments()
                QMessageBox.information(self, "Departamento Actualizado", f"Departamento actualizado a '{updated_dept.name}'.")

        except ValueError as e: # Catch validation errors from service
             print(f"Error saving department: {e}")
             QMessageBox.warning(self, "Error al Guardar", str(e))
        except Exception as e: # Catch unexpected errors
             print(f"Unexpected error saving department: {e}")
             import traceback
             traceback.print_exc()
             QMessageBox.critical(self, "Error Inesperado", f"Ocurrió un error al guardar: {e}")


    @Slot()
    def _delete_department(self):
        """Deletes the selected department after confirmation."""
        selected_item = self.dept_list_widget.currentItem()
        if not selected_item or self._current_department_id is None:
            return # Should not happen if button state is correct

        department: Department = selected_item.data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(self, "Confirmar Eliminación",
                                     f"¿Está seguro que desea eliminar el departamento '{department.name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.product_service.delete_department(department.id)
                # No need to clear form here, _load_departments handles it
                self._load_departments()
                QMessageBox.information(self, "Departamento Eliminado", f"Departamento '{department.name}' eliminado.")
            except ValueError as e: # Catch potential service errors (e.g., department in use)
                QMessageBox.warning(self, "Error al Eliminar", str(e))
            except Exception as e: # Catch other unexpected errors
                QMessageBox.critical(self, "Error Inesperado", f"Ocurrió un error al eliminar: {e}")


# Example of running this dialog directly (for testing)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Use the mock service for testing
    mock_service = MockProductService_Departments()
    dialog = DepartmentDialog(mock_service)
    dialog.exec() # Use exec_() for PySide older versions if needed
    sys.exit() # Exit after dialog closes 