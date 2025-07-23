from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox,
    QFileDialog, QMessageBox, QProgressBar, QTextEdit, QTabWidget, QWidget
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QIcon
import os
from datetime import datetime

from core.services.data_import_export_service import DataImportExportService
from ui.resources import resources  # Import the compiled resources


class ImportExportWorker(QThread):
    """Worker thread para operaciones de importación/exportación."""
    
    progress_updated = Signal(str)  # Mensaje de progreso
    operation_completed = Signal(dict)  # Resultado de la operación
    
    def __init__(self, operation_type, file_path, service):
        super().__init__()
        self.operation_type = operation_type
        self.file_path = file_path
        self.service = service
    
    def run(self):
        """Ejecuta la operación en el hilo de trabajo."""
        try:
            if self.operation_type == "export_excel":
                self.progress_updated.emit("Exportando productos a Excel...")
                result = self.service.export_products_to_excel(self.file_path)
            elif self.operation_type == "export_csv":
                self.progress_updated.emit("Exportando productos a CSV...")
                result = self.service.export_products_to_csv(self.file_path)
            elif self.operation_type == "import_excel":
                self.progress_updated.emit("Importando productos desde Excel...")
                result = self.service.import_products_from_excel(self.file_path)
            elif self.operation_type == "import_csv":
                self.progress_updated.emit("Importando productos desde CSV...")
                result = self.service.import_products_from_csv(self.file_path)
            elif self.operation_type == "create_backup":
                self.progress_updated.emit("Creando respaldo...")
                result = self.service.create_backup(self.file_path)
            elif self.operation_type == "restore_backup":
                self.progress_updated.emit("Restaurando desde respaldo...")
                result = self.service.restore_from_backup(self.file_path)
            else:
                result = {"success": False, "error": "Operación no válida"}
            
            self.operation_completed.emit(result)
            
        except Exception as e:
            self.operation_completed.emit({
                "success": False,
                "error": str(e),
                "message": f"Error durante la operación: {e}"
            })


class ImportExportDialog(QDialog):
    """Diálogo para importar y exportar datos del inventario."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = DataImportExportService()
        self.worker = None
        
        self.setWindowTitle("Importar/Exportar Inventario")
        self.setModal(True)
        self.resize(600, 500)
        
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """Inicializa la interfaz de usuario."""
        layout = QVBoxLayout(self)
        
        # Crear tabs
        self.tab_widget = QTabWidget()
        
        # Tab de Exportación
        export_tab = self._create_export_tab()
        self.tab_widget.addTab(export_tab, "Exportar")
        
        # Tab de Importación
        import_tab = self._create_import_tab()
        self.tab_widget.addTab(import_tab, "Importar")
        
        # Tab de Respaldo
        backup_tab = self._create_backup_tab()
        self.tab_widget.addTab(backup_tab, "Respaldo")
        
        layout.addWidget(self.tab_widget)
        
        # Área de progreso
        progress_group = QGroupBox("Progreso")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_label = QLabel("Listo")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        self.result_text = QTextEdit()
        self.result_text.setMaximumHeight(100)
        self.result_text.setPlaceholderText("Los resultados de las operaciones aparecerán aquí...")
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.result_text)
        
        layout.addWidget(progress_group)
        
        # Botones
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_button = QPushButton("Cerrar")
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def _create_export_tab(self):
        """Crea el tab de exportación."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Grupo de exportación
        export_group = QGroupBox("Exportar Inventario")
        export_layout = QVBoxLayout(export_group)
        
        export_layout.addWidget(QLabel("Seleccione el formato de exportación:"))
        
        # Botón para exportar a Excel
        self.export_excel_btn = QPushButton("Exportar a Excel (.xlsx)")
        self.export_excel_btn.setIcon(QIcon(":/icons/icons/export.png"))
        export_layout.addWidget(self.export_excel_btn)
        
        # Botón para exportar a CSV
        self.export_csv_btn = QPushButton("Exportar a CSV (.csv)")
        self.export_csv_btn.setIcon(QIcon(":/icons/icons/export.png"))
        export_layout.addWidget(self.export_csv_btn)
        
        export_layout.addWidget(QLabel(
            "La exportación incluirá todos los productos con sus códigos, "
            "descripciones, precios, stock y departamentos."
        ))
        
        layout.addWidget(export_group)
        layout.addStretch()
        
        return tab
    
    def _create_import_tab(self):
        """Crea el tab de importación."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Grupo de importación
        import_group = QGroupBox("Importar Inventario")
        import_layout = QVBoxLayout(import_group)
        
        import_layout.addWidget(QLabel("Seleccione el archivo a importar:"))
        
        # Botón para importar desde Excel
        self.import_excel_btn = QPushButton("Importar desde Excel (.xlsx)")
        self.import_excel_btn.setIcon(QIcon(":/icons/icons/import.png"))
        import_layout.addWidget(self.import_excel_btn)
        
        # Botón para importar desde CSV
        self.import_csv_btn = QPushButton("Importar desde CSV (.csv)")
        self.import_csv_btn.setIcon(QIcon(":/icons/icons/import.png"))
        import_layout.addWidget(self.import_csv_btn)
        
        # Información sobre el formato
        info_label = QLabel(
            "<b>Formato requerido:</b><br>"
            "• Código (obligatorio)<br>"
            "• Descripción (obligatorio)<br>"
            "• Precio Costo<br>"
            "• Precio Venta<br>"
            "• Stock<br>"
            "• Stock Mínimo<br>"
            "• Unidad<br>"
            "• Usa Inventario (Sí/No)<br>"
            "• Departamento<br><br>"
            "<b>Nota:</b> Los productos existentes serán actualizados."
        )
        info_label.setWordWrap(True)
        import_layout.addWidget(info_label)
        
        layout.addWidget(import_group)
        layout.addStretch()
        
        return tab
    
    def _create_backup_tab(self):
        """Crea el tab de respaldo."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Grupo de respaldo
        backup_group = QGroupBox("Respaldo Completo")
        backup_layout = QVBoxLayout(backup_group)
        
        backup_layout.addWidget(QLabel("Gestión de respaldos del sistema:"))
        
        # Botón para crear respaldo
        self.create_backup_btn = QPushButton("Crear Respaldo")
        self.create_backup_btn.setIcon(QIcon(":/icons/icons/backup.png"))
        backup_layout.addWidget(self.create_backup_btn)
        
        # Botón para restaurar respaldo
        self.restore_backup_btn = QPushButton("Restaurar Respaldo")
        self.restore_backup_btn.setIcon(QIcon(":/icons/icons/restore.png"))
        backup_layout.addWidget(self.restore_backup_btn)
        
        # Información sobre respaldos
        backup_info = QLabel(
            "<b>Respaldo:</b> Crea un archivo JSON con todos los datos del sistema "
            "(productos, departamentos, clientes).<br><br>"
            "<b>Restaurar:</b> Restaura los datos desde un archivo de respaldo. "
            "Los datos existentes serán actualizados o creados según corresponda.<br><br>"
            "<b>Recomendación:</b> Cree respaldos regulares para proteger sus datos."
        )
        backup_info.setWordWrap(True)
        backup_layout.addWidget(backup_info)
        
        layout.addWidget(backup_group)
        layout.addStretch()
        
        return tab
    
    def _connect_signals(self):
        """Conecta las señales a los slots."""
        self.export_excel_btn.clicked.connect(self._export_to_excel)
        self.export_csv_btn.clicked.connect(self._export_to_csv)
        self.import_excel_btn.clicked.connect(self._import_from_excel)
        self.import_csv_btn.clicked.connect(self._import_from_csv)
        self.create_backup_btn.clicked.connect(self._create_backup)
        self.restore_backup_btn.clicked.connect(self._restore_backup)
        self.close_button.clicked.connect(self.accept)
    
    def _export_to_excel(self):
        """Exporta productos a Excel."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar a Excel",
            f"inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Archivos Excel (*.xlsx)"
        )
        
        if file_path:
            self._start_operation("export_excel", file_path)
    
    def _export_to_csv(self):
        """Exporta productos a CSV."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar a CSV",
            f"inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "Archivos CSV (*.csv)"
        )
        
        if file_path:
            self._start_operation("export_csv", file_path)
    
    def _import_from_excel(self):
        """Importa productos desde Excel."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar desde Excel",
            "",
            "Archivos Excel (*.xlsx)"
        )
        
        if file_path:
            reply = QMessageBox.question(
                self,
                "Confirmar Importación",
                "¿Está seguro que desea importar los datos?\n\n"
                "Los productos existentes con el mismo código serán actualizados.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self._start_operation("import_excel", file_path)
    
    def _import_from_csv(self):
        """Importa productos desde CSV."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar desde CSV",
            "",
            "Archivos CSV (*.csv)"
        )
        
        if file_path:
            reply = QMessageBox.question(
                self,
                "Confirmar Importación",
                "¿Está seguro que desea importar los datos?\n\n"
                "Los productos existentes con el mismo código serán actualizados.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self._start_operation("import_csv", file_path)
    
    def _create_backup(self):
        """Crea un respaldo completo."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Crear Respaldo",
            f"respaldo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "Archivos JSON (*.json)"
        )
        
        if file_path:
            self._start_operation("create_backup", file_path)
    
    def _restore_backup(self):
        """Restaura desde un respaldo."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Restaurar Respaldo",
            "",
            "Archivos JSON (*.json)"
        )
        
        if file_path:
            reply = QMessageBox.question(
                self,
                "Confirmar Restauración",
                "¿Está seguro que desea restaurar desde este respaldo?\n\n"
                "Los datos existentes serán actualizados o creados según corresponda.\n"
                "Esta operación no se puede deshacer.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self._start_operation("restore_backup", file_path)
    
    def _start_operation(self, operation_type, file_path):
        """Inicia una operación en un hilo separado."""
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Operación en Progreso", "Ya hay una operación en progreso.")
            return
        
        # Configurar UI para mostrar progreso
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminado
        self.result_text.clear()
        
        # Deshabilitar botones
        self._set_buttons_enabled(False)
        
        # Crear y configurar worker
        self.worker = ImportExportWorker(operation_type, file_path, self.service)
        self.worker.progress_updated.connect(self._update_progress)
        self.worker.operation_completed.connect(self._operation_completed)
        self.worker.finished.connect(self._operation_finished)
        
        # Iniciar operación
        self.worker.start()
    
    def _update_progress(self, message):
        """Actualiza el mensaje de progreso."""
        self.progress_label.setText(message)
    
    def _operation_completed(self, result):
        """Maneja la finalización de una operación."""
        if result["success"]:
            self.result_text.setPlainText(f"✓ {result['message']}")
            
            # Mostrar detalles adicionales si están disponibles
            details = []
            if "products_exported" in result:
                details.append(f"Productos exportados: {result['products_exported']}")
            if "imported" in result:
                details.append(f"Productos importados: {result['imported']}")
            if "updated" in result:
                details.append(f"Productos actualizados: {result['updated']}")
            if "skipped" in result:
                details.append(f"Productos omitidos: {result['skipped']}")
            if "errors" in result and result["errors"]:
                details.append(f"Errores: {len(result['errors'])}")
                details.extend([f"  - {error}" for error in result["errors"][:5]])  # Mostrar solo los primeros 5 errores
                if len(result["errors"]) > 5:
                    details.append(f"  ... y {len(result['errors']) - 5} errores más")
            
            if details:
                current_text = self.result_text.toPlainText()
                self.result_text.setPlainText(current_text + "\n\n" + "\n".join(details))
        else:
            error_msg = f"✗ {result['message']}"
            if "error" in result:
                error_msg += f"\n\nDetalle del error: {result['error']}"
            self.result_text.setPlainText(error_msg)
    
    def _operation_finished(self):
        """Limpia después de que termine una operación."""
        self.progress_bar.setVisible(False)
        self.progress_label.setText("Operación completada")
        self._set_buttons_enabled(True)
        
        # Limpiar worker
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
    
    def _set_buttons_enabled(self, enabled):
        """Habilita o deshabilita todos los botones."""
        self.export_excel_btn.setEnabled(enabled)
        self.export_csv_btn.setEnabled(enabled)
        self.import_excel_btn.setEnabled(enabled)
        self.import_csv_btn.setEnabled(enabled)
        self.create_backup_btn.setEnabled(enabled)
        self.restore_backup_btn.setEnabled(enabled)
    
    def closeEvent(self, event):
        """Maneja el cierre del diálogo."""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Operación en Progreso",
                "Hay una operación en progreso. ¿Desea cancelarla y cerrar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.terminate()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()