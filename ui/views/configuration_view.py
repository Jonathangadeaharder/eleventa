from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QMessageBox,
    QHBoxLayout,
    QScrollArea,
)
from PySide6.QtCore import Qt

from config import config


class ConfigurationView(QWidget):
    """Configuration view for editing store information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("configuration_view")

        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Create scroll area for configuration (in case it grows in the future)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)

        # Create store information group
        store_group = QGroupBox("Información de la Tienda")
        store_layout = QFormLayout()
        store_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        store_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )

        # Store name field
        self.store_name_edit = QLineEdit()
        self.store_name_edit.setPlaceholderText("Nombre de la tienda")
        store_layout.addRow("Nombre:", self.store_name_edit)

        # Store address field
        self.store_address_edit = QLineEdit()
        self.store_address_edit.setPlaceholderText("Dirección de la tienda")
        store_layout.addRow("Dirección:", self.store_address_edit)

        # Store CUIT field
        self.store_cuit_edit = QLineEdit()
        self.store_cuit_edit.setPlaceholderText("CUIT (formato: xx-xxxxxxxx-x)")
        store_layout.addRow("CUIT:", self.store_cuit_edit)

        # Store IVA condition field
        self.store_iva_edit = QLineEdit()
        self.store_iva_edit.setPlaceholderText("Condición IVA")
        store_layout.addRow("Condición IVA:", self.store_iva_edit)

        # Store phone field
        self.store_phone_edit = QLineEdit()
        self.store_phone_edit.setPlaceholderText("Teléfono (opcional)")
        store_layout.addRow("Teléfono:", self.store_phone_edit)

        store_group.setLayout(store_layout)
        scroll_layout.addWidget(store_group)

        # Add future configuration groups here
        # Example: receipt_group = QGroupBox("Configuración de Recibos")

        # Create buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        # Save button
        self.save_button = QPushButton("Guardar Configuración")
        self.save_button.clicked.connect(self.save_configuration)
        buttons_layout.addWidget(self.save_button)

        scroll_layout.addLayout(buttons_layout)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # Load current configuration
        self.load_configuration()

    def load_configuration(self):
        """Load configuration values into the form fields."""
        self.store_name_edit.setText(config.STORE_NAME)
        self.store_address_edit.setText(config.STORE_ADDRESS)
        self.store_cuit_edit.setText(config.STORE_CUIT)
        self.store_iva_edit.setText(config.STORE_IVA_CONDITION)
        self.store_phone_edit.setText(config.STORE_PHONE)

    def save_configuration(self):
        """Save configuration values from the form fields."""
        try:
            # Update config instance attributes
            config.store_name = self.store_name_edit.text()
            config.store_address = self.store_address_edit.text()
            config.store_cuit = self.store_cuit_edit.text()
            config.store_iva_condition = self.store_iva_edit.text()
            config.store_phone = self.store_phone_edit.text()

            # Save to .env file for persistence
            if config.save_to_env_file():
                # Show success message
                QMessageBox.information(
                    self,
                    "Configuración Guardada",
                    "Los cambios han sido guardados exitosamente y se mantendrán entre sesiones.",
                )
            else:
                # Show warning if file save failed
                QMessageBox.warning(
                    self,
                    "Advertencia",
                    "Los cambios se aplicaron en memoria pero no se pudieron guardar en el archivo .env.\n"
                    "Los cambios se perderán al reiniciar la aplicación.",
                )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error al Guardar",
                f"No se pudo guardar la configuración: {str(e)}",
            )
