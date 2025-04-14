import unittest
from core.models.user import User

class TestUserModel(unittest.TestCase):

    def test_user_creation_defaults(self):
        """Test creating a User with default values."""
        user = User(username="testuser", password_hash="some_hash")
        self.assertIsNone(user.id)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.password_hash, "some_hash")
        self.assertTrue(user.is_active)

    def test_user_creation_with_id_and_inactive(self):
        """Test creating a User with specific ID and inactive status."""
        user = User(id=123, username="anotheruser", password_hash="another_hash", is_active=False)
        self.assertEqual(user.id, 123)
        self.assertEqual(user.username, "anotheruser")
        self.assertEqual(user.password_hash, "another_hash")
        self.assertFalse(user.is_active)

if __name__ == '__main__':
    unittest.main()
