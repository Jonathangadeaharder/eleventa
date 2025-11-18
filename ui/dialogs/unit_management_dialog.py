from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QCheckBox,
    QLabel,
    QMessageBox,
    QHeaderView,
    QAbstractItemView,
    QGroupBox,
    QFormLayout,
    QComboBox,
)
from PySide6.QtCore import Qt, Signal
from typing import List, Optional
import logging

from core.models.unit import Unit
from core.models.enums import StandardUnitType
from core.services.unit_service import UnitService
from ui.styles.style_manager import StyleManager


class UnitManagementDialog(QDialog):
    """Dialog for managing custom unit categories."""

    units_changed = Signal()  # Signal emitted when units are modified

    def __init__(self, parent=None):
        super().__init__(parent)
        self.unit_service = UnitService()
        self.units: List[Unit] = []
        self.selected_unit: Optional[Unit] = None

        self.setWindowTitle("Gestión de Unidades")
        self.setModal(True)
        self.resize(800, 600)

        self.setup_ui()
        self.apply_styles()
        self.load_units()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("Gestión de Unidades de Medida")
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)

        # Main content layout
        content_layout = QHBoxLayout()

        # Left side - Unit list
        left_group = QGroupBox("Unidades Existentes")
        left_layout = QVBoxLayout(left_group)

        # Search box
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre o abreviación...")
        self.search_input.textChanged.connect(self.filter_units)
        search_layout.addWidget(self.search_input)
        left_layout.addLayout(search_layout)

        # Units table
        self.units_table = QTableWidget()
        self.units_table.setColumnCount(4)
        self.units_table.setHorizontalHeaderLabels(
            ["Nombre", "Abreviación", "Descripción", "Activo"]
        )
        self.units_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.units_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.units_table.itemSelectionChanged.connect(self.on_unit_selected)

        # Configure table columns
        header = self.units_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Name
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )  # Abbreviation
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Description
        header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )  # Active

        left_layout.addWidget(self.units_table)

        # Table buttons
        table_buttons_layout = QHBoxLayout()
        self.delete_button = QPushButton("Eliminar")
        self.delete_button.clicked.connect(self.delete_unit)
        self.delete_button.setEnabled(False)

        self.toggle_status_button = QPushButton("Activar/Desactivar")
        self.toggle_status_button.clicked.connect(self.toggle_unit_status)
        self.toggle_status_button.setEnabled(False)

        table_buttons_layout.addWidget(self.delete_button)
        table_buttons_layout.addWidget(self.toggle_status_button)
        table_buttons_layout.addStretch()
        left_layout.addLayout(table_buttons_layout)

        content_layout.addWidget(left_group, 2)

        # Right side - Unit form
        right_group = QGroupBox("Agregar/Editar Unidad")
        right_layout = QVBoxLayout(right_group)

        # Standard units section
        standard_group = QGroupBox("Unidades Estándar")
        standard_layout = QFormLayout(standard_group)

        self.standard_unit_combo = QComboBox()
        self.standard_unit_combo.addItem("Seleccionar unidad estándar...", None)
        for unit_type in StandardUnitType:
            self.standard_unit_combo.addItem(unit_type.value, unit_type)
        self.standard_unit_combo.currentIndexChanged.connect(
            self.on_standard_unit_selected
        )
        standard_layout.addRow("Unidad:", self.standard_unit_combo)

        self.add_standard_button = QPushButton("Agregar Unidad Estándar")
        self.add_standard_button.clicked.connect(self.add_standard_unit)
        self.add_standard_button.setEnabled(False)
        standard_layout.addRow("", self.add_standard_button)

        right_layout.addWidget(standard_group)

        # Custom unit form
        custom_group = QGroupBox("Unidad Personalizada")
        form_layout = QFormLayout(custom_group)

        self.name_input = QLineEdit()
        self.name_input.setMaxLength(50)
        self.name_input.textChanged.connect(self.validate_form)
        form_layout.addRow("Nombre*:", self.name_input)

        self.abbreviation_input = QLineEdit()
        self.abbreviation_input.setMaxLength(10)
        self.abbreviation_input.textChanged.connect(self.validate_form)
        form_layout.addRow("Abreviación*:", self.abbreviation_input)

        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        form_layout.addRow("Descripción:", self.description_input)

        self.is_active_checkbox = QCheckBox("Activo")
        self.is_active_checkbox.setChecked(True)
        form_layout.addRow("", self.is_active_checkbox)

        right_layout.addWidget(custom_group)

        # Form buttons
        form_buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save_unit)
        self.save_button.setEnabled(False)

        self.clear_button = QPushButton("Limpiar")
        self.clear_button.clicked.connect(self.clear_form)

        form_buttons_layout.addWidget(self.save_button)
        form_buttons_layout.addWidget(self.clear_button)
        form_buttons_layout.addStretch()
        right_layout.addLayout(form_buttons_layout)

        right_layout.addStretch()
        content_layout.addWidget(right_group, 1)

        layout.addLayout(content_layout)

        # Dialog buttons
        dialog_buttons_layout = QHBoxLayout()
        self.close_button = QPushButton("Cerrar")
        self.close_button.clicked.connect(self.accept)
        dialog_buttons_layout.addStretch()
        dialog_buttons_layout.addWidget(self.close_button)
        layout.addLayout(dialog_buttons_layout)

    def apply_styles(self):
        """Apply styles to the dialog."""
        try:
            StyleManager.apply_style(self, "dialog")
        except Exception as e:
            logging.warning(f"Could not apply styles: {e}")

    def load_units(self):
        """Load units from the database."""
        try:
            self.units = self.unit_service.get_all_units(active_only=False)
            self.populate_table()
        except Exception as e:
            logging.error(f"Error loading units: {e}")
            QMessageBox.critical(self, "Error", f"Error al cargar las unidades: {e}")

    def populate_table(self, units: Optional[List[Unit]] = None):
        """Populate the units table."""
        if units is None:
            units = self.units

        self.units_table.setRowCount(len(units))

        for row, unit in enumerate(units):
            # Name
            name_item = QTableWidgetItem(unit.name)
            name_item.setData(Qt.ItemDataRole.UserRole, unit)
            self.units_table.setItem(row, 0, name_item)

            # Abbreviation
            self.units_table.setItem(row, 1, QTableWidgetItem(unit.abbreviation or ""))

            # Description
            self.units_table.setItem(row, 2, QTableWidgetItem(unit.description or ""))

            # Active status
            status_item = QTableWidgetItem("Sí" if unit.is_active else "No")
            if not unit.is_active:
                status_item.setForeground(Qt.GlobalColor.red)
            self.units_table.setItem(row, 3, status_item)

    def filter_units(self):
        """Filter units based on search text."""
        search_text = self.search_input.text().lower().strip()

        if not search_text:
            filtered_units = self.units
        else:
            filtered_units = [
                unit
                for unit in self.units
                if (
                    search_text in unit.name.lower()
                    or search_text in (unit.abbreviation or "").lower()
                )
            ]

        self.populate_table(filtered_units)

    def on_unit_selected(self):
        """Handle unit selection in the table."""
        current_row = self.units_table.currentRow()
        if current_row >= 0:
            name_item = self.units_table.item(current_row, 0)
            if name_item:
                self.selected_unit = name_item.data(Qt.ItemDataRole.UserRole)
                self.delete_button.setEnabled(True)
                self.toggle_status_button.setEnabled(True)
                self.load_unit_to_form(self.selected_unit)
            else:
                self.selected_unit = None
                self.delete_button.setEnabled(False)
                self.toggle_status_button.setEnabled(False)
        else:
            self.selected_unit = None
            self.delete_button.setEnabled(False)
            self.toggle_status_button.setEnabled(False)

    def load_unit_to_form(self, unit: Unit):
        """Load unit data into the form for editing."""
        self.name_input.setText(unit.name)
        self.abbreviation_input.setText(unit.abbreviation or "")
        self.description_input.setPlainText(unit.description or "")
        self.is_active_checkbox.setChecked(unit.is_active)

    def on_standard_unit_selected(self):
        """Handle standard unit selection."""
        current_data = self.standard_unit_combo.currentData()
        self.add_standard_button.setEnabled(current_data is not None)

    def add_standard_unit(self):
        """Add a selected standard unit."""
        unit_type = self.standard_unit_combo.currentData()
        if not unit_type:
            return

        # Check if unit already exists
        existing = next((u for u in self.units if u.name == unit_type.value), None)
        if existing:
            QMessageBox.information(
                self, "Información", f"La unidad '{unit_type.value}' ya existe."
            )
            return

        # Create unit based on standard type
        abbreviations = {
            StandardUnitType.UNIDAD: "Ud",
            StandardUnitType.KILOGRAMO: "Kg",
            StandardUnitType.LITRO: "L",
            StandardUnitType.CAJA: "Cj",
        }

        descriptions = {
            StandardUnitType.UNIDAD: "Unidad individual",
            StandardUnitType.KILOGRAMO: "Unidad de peso",
            StandardUnitType.LITRO: "Unidad de volumen",
            StandardUnitType.CAJA: "Caja o paquete",
        }

        unit = Unit(
            name=unit_type.value,
            abbreviation=abbreviations.get(unit_type, ""),
            description=descriptions.get(unit_type, ""),
            is_active=True,
        )

        try:
            saved_unit = self.unit_service.add_unit(unit)
            self.units.append(saved_unit)
            self.populate_table()
            self.units_changed.emit()

            # Reset combo
            self.standard_unit_combo.setCurrentIndex(0)
            self.add_standard_button.setEnabled(False)

            QMessageBox.information(
                self, "Éxito", f"Unidad '{unit.name}' agregada exitosamente."
            )

        except Exception as e:
            logging.error(f"Error adding standard unit: {e}")
            QMessageBox.critical(self, "Error", f"Error al agregar la unidad: {e}")

    def validate_form(self):
        """Validate the form and enable/disable save button."""
        name = self.name_input.text().strip()
        abbreviation = self.abbreviation_input.text().strip()

        is_valid = bool(name and abbreviation)
        self.save_button.setEnabled(is_valid)

    def save_unit(self):
        """Save the unit (add or update)."""
        name = self.name_input.text().strip()
        abbreviation = self.abbreviation_input.text().strip()
        description = self.description_input.toPlainText().strip()
        is_active = self.is_active_checkbox.isChecked()

        if not name or not abbreviation:
            QMessageBox.warning(
                self, "Advertencia", "El nombre y la abreviación son obligatorios."
            )
            return

        try:
            if self.selected_unit and self.selected_unit.id:
                # Update existing unit
                unit = Unit(
                    id=self.selected_unit.id,
                    name=name,
                    abbreviation=abbreviation,
                    description=description,
                    is_active=is_active,
                    created_at=self.selected_unit.created_at,
                    updated_at=self.selected_unit.updated_at,
                )
                updated_unit = self.unit_service.update_unit(unit)

                # Update in local list
                for i, u in enumerate(self.units):
                    if u.id == updated_unit.id:
                        self.units[i] = updated_unit
                        break

                QMessageBox.information(
                    self, "Éxito", "Unidad actualizada exitosamente."
                )
            else:
                # Add new unit
                unit = Unit(
                    name=name,
                    abbreviation=abbreviation,
                    description=description,
                    is_active=is_active,
                )
                saved_unit = self.unit_service.add_unit(unit)
                self.units.append(saved_unit)

                QMessageBox.information(self, "Éxito", "Unidad agregada exitosamente.")

            self.populate_table()
            self.clear_form()
            self.units_changed.emit()

        except Exception as e:
            logging.error(f"Error saving unit: {e}")
            QMessageBox.critical(self, "Error", f"Error al guardar la unidad: {e}")

    def clear_form(self):
        """Clear the form fields."""
        self.name_input.clear()
        self.abbreviation_input.clear()
        self.description_input.clear()
        self.is_active_checkbox.setChecked(True)
        self.selected_unit = None
        self.save_button.setEnabled(False)

        # Clear table selection
        self.units_table.clearSelection()
        self.delete_button.setEnabled(False)
        self.toggle_status_button.setEnabled(False)

    def delete_unit(self):
        """Delete the selected unit."""
        if not self.selected_unit:
            return

        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar la unidad '{self.selected_unit.name}'?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.unit_service.delete_unit(self.selected_unit.id)

                # Remove from local list
                self.units = [u for u in self.units if u.id != self.selected_unit.id]
                self.populate_table()
                self.clear_form()
                self.units_changed.emit()

                QMessageBox.information(self, "Éxito", "Unidad eliminada exitosamente.")

            except Exception as e:
                logging.error(f"Error deleting unit: {e}")
                QMessageBox.critical(self, "Error", f"Error al eliminar la unidad: {e}")

    def toggle_unit_status(self):
        """Toggle the active status of the selected unit."""
        if not self.selected_unit:
            return

        try:
            updated_unit = self.unit_service.toggle_unit_status(self.selected_unit.id)

            # Update in local list
            for i, u in enumerate(self.units):
                if u.id == updated_unit.id:
                    self.units[i] = updated_unit
                    break

            self.populate_table()
            self.load_unit_to_form(updated_unit)
            self.units_changed.emit()

            status = "activada" if updated_unit.is_active else "desactivada"
            QMessageBox.information(self, "Éxito", f"Unidad {status} exitosamente.")

        except Exception as e:
            logging.error(f"Error toggling unit status: {e}")
            QMessageBox.critical(
                self, "Error", f"Error al cambiar el estado de la unidad: {e}"
            )
