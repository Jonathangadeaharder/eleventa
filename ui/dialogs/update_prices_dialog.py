from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
    QComboBox, QDialogButtonBox
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QDoubleValidator
from decimal import Decimal, InvalidOperation

from core.services.product_service import ProductService
from core.models.product import Department

class UpdatePricesDialog(QDialog):
    def __init__(self, product_service: ProductService, parent=None):
        super().__init__(parent)
        self.product_service = product_service
        self.setWindowTitle("Actualizar Precios de Productos")
        self.setMinimumWidth(400)

        self.departments: list[Department] = []

        layout = QVBoxLayout(self)

        # Percentage input
        percentage_layout = QHBoxLayout()
        percentage_label = QLabel("Porcentaje de Aumento/Disminución (%):")
        self.percentage_input = QLineEdit()
        self.percentage_input.setPlaceholderText("Ej: 10 para aumentar, -5 para disminuir")
        # Allow positive and negative numbers, and decimals
        validator = QDoubleValidator(-99.99, 999.99, 2, self)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.percentage_input.setValidator(validator)
        percentage_layout.addWidget(percentage_label)
        percentage_layout.addWidget(self.percentage_input)
        layout.addLayout(percentage_layout)

        # Department selection
        department_layout = QHBoxLayout()
        department_label = QLabel("Departamento:")
        self.department_combo = QComboBox()
        self.department_combo.addItem("Todos los Departamentos", None) # Option for all
        department_layout.addWidget(department_label)
        department_layout.addWidget(self.department_combo)
        layout.addLayout(department_layout)

        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.load_departments()

    def load_departments(self):
        try:
            self.departments = self.product_service.get_all_departments()
            for dept in self.departments:
                self.department_combo.addItem(dept.name, dept.id)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los departamentos: {e}")

    def get_selected_department_id(self) -> int | None:
        return self.department_combo.currentData()

    def get_percentage(self) -> Decimal | None:
        text = self.percentage_input.text().replace(",", ".") # Allow comma as decimal separator
        if not text:
            QMessageBox.warning(self, "Entrada Inválida", "Por favor ingrese un porcentaje.")
            return None
        try:
            # Ensure it's treated as Decimal, respecting the validator
            # The validator handles basic format, but we need to ensure it's a valid number
            val = Decimal(text)
            if val <= Decimal("-100"):
                 QMessageBox.warning(self, "Entrada Inválida", "El porcentaje debe ser mayor que -100%.")
                 return None
            return val
        except InvalidOperation:
            QMessageBox.warning(self, "Entrada Inválida", "Porcentaje inválido. Use números (ej: 10.5 o -5).")
            return None

    @Slot()
    def accept(self):
        percentage = self.get_percentage()
        if percentage is None:
            return # Error message already shown

        department_id = self.get_selected_department_id()
        department_name = self.department_combo.currentText()

        confirm_msg = f"¿Está seguro que desea actualizar los precios en un {percentage}% "
        if department_id:
            confirm_msg += f"para el departamento '{department_name}'?"
        else:
            confirm_msg += f"para TODOS los productos?"

        reply = QMessageBox.question(self, "Confirmar Actualización", confirm_msg,
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                updated_count = self.product_service.update_prices_by_percentage(percentage, department_id)
                QMessageBox.information(self, "Éxito", f"Se actualizaron los precios de {updated_count} producto(s).")
                super().accept()
            except ValueError as ve:
                QMessageBox.critical(self, "Error de Validación", str(ve))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Ocurrió un error al actualizar los precios: {e}")
        # If No, do nothing, dialog remains open

    @staticmethod
    def run_update_prices_dialog(product_service: ProductService, parent=None) -> bool:
        dialog = UpdatePricesDialog(product_service, parent)
        return dialog.exec() == QDialog.Accepted

if __name__ == '__main__':
    # This is for testing the dialog independently
    from PySide6.QtWidgets import QApplication
    import sys

    # Mock ProductService and Departments for testing
    class MockDepartmentRepository:
        def get_all(self):
            return [
                Department(id=1, name="Electrónica", description="Artículos electrónicos"),
                Department(id=2, name="Ropa", description="Vestimenta y accesorios"),
                Department(id=3, name="Hogar", description="Artículos para el hogar"),
            ]
        # Add other methods if ProductService needs them during init or other calls
        def get_by_id(self, id): return None
        def get_by_name(self, name): return None
        def add(self, dept): return dept
        def update(self, dept): return dept
        def delete(self, id): return True


    class MockProductRepository:
        def get_by_department_id(self, department_id):
            print(f"Mock: getting products for department {department_id}")
            # Simulate some products
            if department_id == 1:
                return [Product(id=1, code="P001", description="TV", sell_price=Decimal("500.00"), department_id=1)]
            return []

        def get_all(self):
            print("Mock: getting all products")
            return [
                Product(id=1, code="P001", description="TV", sell_price=Decimal("500.00"), department_id=1),
                Product(id=2, code="P002", description="Camisa", sell_price=Decimal("25.00"), department_id=2),
            ]
        
        def update(self, product):
            print(f"Mock: updating product {product.id} with new price {product.sell_price}")
            # In a real scenario, this would persist the change
            pass

        # Add other methods if ProductService needs them
        def add(self, prod): return prod
        def get_by_id(self, id): return None
        def get_by_code(self, code): return None
        def delete(self, id): return True
        def search(self, term): return []
        def get_low_stock(self, limit): return []
        def update_stock(self, prod_id, qty, cost): return None


    # Dummy session factory
    def mock_session_factory(repo_factory, session_param):
        return repo_factory(session_param)


    app = QApplication(sys.argv)
    
    # Create mock repositories
    mock_dept_repo = MockDepartmentRepository()
    mock_prod_repo = MockProductRepository()

    # Factory functions for the service
    def product_repo_factory(session): return mock_prod_repo
    def department_repo_factory(session): return mock_dept_repo

    # Instantiate the service with mock repositories
    # The service expects factories that take a session, but our mocks don't use a session.
    # So, we wrap them in lambdas.
    product_service_mock = ProductService(
        product_repo_factory=lambda s: mock_prod_repo, # s is the dummy session
        department_repo_factory=lambda s: mock_dept_repo
    )
    
    # Test the actual service method via a mock
    original_update_prices = product_service_mock.update_prices_by_percentage
    update_call_args = {}
    def mock_update_prices_by_percentage(percentage, department_id=None):
        update_call_args = {"percentage": percentage, "department_id": department_id}
        print(f"Mock ProductService: update_prices_by_percentage called with {percentage=}, {department_id=}")
        # Simulate some products updated
        if department_id:
            return 1 
        return 2 
    product_service_mock.update_prices_by_percentage = mock_update_prices_by_percentage


    dialog_executed = UpdatePricesDialog.run_update_prices_dialog(product_service_mock)
    if dialog_executed:
        print("Dialog accepted, mock service called with:", update_call_args)
    else:
        print("Dialog cancelled.")
    
    # Example of direct service call (for debugging service logic)
    # try:
    #     product_service_mock.update_prices_by_percentage = original_update_prices # restore
    #     count = product_service_mock.update_prices_by_percentage(Decimal("10"), 1)
    #     print(f"Direct service call updated {count} products.")
    #     count_all = product_service_mock.update_prices_by_percentage(Decimal("-5"))
    #     print(f"Direct service call updated {count_all} products (all).")
    # except Exception as e:
    #     print(f"Error in direct service call: {e}")

    sys.exit() # QApplication.exec() is not needed if dialog.exec() is used 