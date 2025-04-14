import unittest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
import sys

# Ensure QApplication exists
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

from ui.dialogs.login_dialog import LoginDialog

class TestLoginDialog(unittest.TestCase):
    def setUp(self):
        self.mock_user_service = MagicMock()
        self.dialog = LoginDialog(self.mock_user_service)

    def tearDown(self):
        self.dialog.close()

    def test_successful_login(self):
        # Mock user_service to return a user object
        mock_user = MagicMock()
        self.mock_user_service.authenticate_user.return_value = mock_user

        self.dialog.username_input.setText("testuser")
        self.dialog.password_input.setText("password123")
        QTest.mouseClick(self.dialog.login_button, Qt.LeftButton)

        self.assertEqual(self.dialog.result(), QDialog.Accepted)
        self.assertEqual(self.dialog.logged_in_user, mock_user)

    def test_failed_login_invalid_credentials(self):
        # Mock user_service to return None (invalid credentials)
        self.mock_user_service.authenticate_user.return_value = None

        self.dialog.username_input.setText("wronguser")
        self.dialog.password_input.setText("wrongpass")
        with unittest.mock.patch.object(QMessageBox, 'warning') as mock_warning:
            QTest.mouseClick(self.dialog.login_button, Qt.LeftButton)
            self.assertEqual(self.dialog.result(), 0)  # Not accepted
            self.assertIsNone(self.dialog.logged_in_user)
            mock_warning.assert_called_once()
            # Password field should be cleared
            self.assertEqual(self.dialog.password_input.text(), "")

    def test_empty_fields_shows_warning(self):
        self.dialog.username_input.setText("")
        self.dialog.password_input.setText("")
        with unittest.mock.patch.object(QMessageBox, 'warning') as mock_warning:
            QTest.mouseClick(self.dialog.login_button, Qt.LeftButton)
            mock_warning.assert_called_once()
            self.assertEqual(self.dialog.result(), 0)
            self.assertIsNone(self.dialog.logged_in_user)

    def test_authentication_exception_shows_critical(self):
        # Mock user_service to raise an exception
        self.mock_user_service.authenticate_user.side_effect = Exception("DB error")
        self.dialog.username_input.setText("testuser")
        self.dialog.password_input.setText("password123")
        with unittest.mock.patch.object(QMessageBox, 'critical') as mock_critical:
            QTest.mouseClick(self.dialog.login_button, Qt.LeftButton)
            mock_critical.assert_called_once()
            self.assertEqual(self.dialog.result(), 0)
            self.assertIsNone(self.dialog.logged_in_user)

if __name__ == "__main__":
    unittest.main()