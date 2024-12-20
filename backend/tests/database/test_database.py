import unittest
from unittest.mock import patch, MagicMock
from src.database.database import register_user, login_user, fetch_vps_data
from src.database.database_exceptions import UserRegistrationError, UserLoginError, VPSDataFetchError


class TestDatabase(unittest.TestCase):

    @patch('src.database.database.pyodbc.connect')
    def test_register_user_success(self, mock_connect):
        # Setup
        mock_cursor = MagicMock()
        mock_cursor.fetchval.return_value = 1
        mock_connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        # Execute
        user_id, error = register_user('testuser', 'test@example.com', 'password123')

        # Assert
        self.assertEqual(user_id, 1)
        self.assertIsNone(error)
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchval.assert_called_once()

    @patch('src.database.database.pyodbc.connect')
    def test_register_user_username_exists(self, mock_connect):
        # Setup
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = UserRegistrationError("Username already exists")

        # Execute
        user_id, error = register_user('existinguser', 'test@example.com', 'password123')

        # Assert
        self.assertIsNone(user_id)
        self.assertEqual(error, "Username already exists")

    @patch('src.database.database.pyodbc.connect')
    @patch('src.database.database.bcrypt.checkpw')
    def test_login_user_success(self, mock_checkpw, mock_connect):
        # Setup
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, 0, 'hashed_password')
        mock_connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_checkpw.return_value = True

        # Execute
        user_id, error = login_user('test@example.com', 'password123')

        # Assert
        self.assertEqual(user_id, 1)
        self.assertIsNone(error)
        mock_cursor.execute.assert_called()
        mock_checkpw.assert_called_once()

    @patch('src.database.database.pyodbc.connect')
    def test_login_user_invalid_credentials(self, mock_connect):
        # Setup
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (None, -1, None)
        mock_connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        # Execute
        user_id, error = login_user('nonexistent@example.com', 'wrongpassword')

        # Assert
        self.assertIsNone(user_id)
        self.assertEqual(error, "User not found")

    @patch('src.database.database.pyodbc.connect')
    def test_login_user_database_error(self, mock_connect):
        # Setup
        mock_connect.side_effect = UserLoginError("An error occurred during login")

        # Execute and Assert
        with self.assertRaises(UserLoginError) as context:
            login_user('test@example.com', 'password123')

        self.assertEqual(str(context.exception), "An error occurred during login")

    @patch('src.database.database.pyodbc.connect')
    @patch('src.database.database.decrypt_data')
    def test_fetch_vps_data_success(self, mock_decrypt, mock_connect):
        # Setup
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (
            '192.168.1.1', b'encrypted_pub', b'encrypted_priv', b'encrypted_pass', b'fernet_key', 'Test Project')
        mock_connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_decrypt.side_effect = ['decrypted_pub', 'decrypted_priv', 'decrypted_pass']

        # Execute
        result = fetch_vps_data(1)

        # Assert
        self.assertEqual(result, {
            'ip': '192.168.1.1',
            'wallet': 'decrypted_pub',
            'priv_key': 'decrypted_priv',
            'password': 'decrypted_pass',
            'project_name': 'Test Project'
        })
        mock_cursor.execute.assert_called_once()
        self.assertEqual(mock_decrypt.call_count, 3)

    @patch('src.database.database.pyodbc.connect')
    def test_fetch_vps_data_not_found(self, mock_connect):
        # Setup
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        # Execute and Assert
        with self.assertRaises(VPSDataFetchError):
            fetch_vps_data(999)


if __name__ == '__main__':
    unittest.main()
