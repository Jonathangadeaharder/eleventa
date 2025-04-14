import pytest
from PySide6.QtWidgets import QApplication, QLabel
from ui.views.corte_view import CorteView

import sys

# Minimal CorteService mock
class DummyCorteService:
    def calculate_corte_data(self, *args, **kwargs):
        return {}
    def finalize_corte(self, *args, **kwargs):
        return True

@pytest.fixture(scope="module")
def app():
    """Ensure a QApplication exists for the tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

def test_corte_view_instantiation(app):
    """Smoke test: CorteView can be instantiated and shown."""
    corte_service = DummyCorteService()
    view = CorteView(corte_service)
    view.show()
    assert view.windowTitle() == "" or isinstance(view, CorteView)
    # Check for the title label
    found = False
    # Find all QLabel children directly
    for child in view.findChildren(QLabel):
        if hasattr(child, "text") and child.text() == "Corte de Caja":
            found = True
            break
    assert found, "Title label 'Corte de Caja' not found in CorteView"