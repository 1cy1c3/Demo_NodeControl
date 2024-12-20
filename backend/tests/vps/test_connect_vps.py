import unittest
from unittest.mock import patch, MagicMock
from src.vps.connect_vps import setup_server, setup_vps, setup_vps_async
from src.vps.vps_exceptions import (
    VPSConnectionError, VPSAuthenticationError, VPSFileOperationError,
    VPSSetupError, VPSExecutionError
)
import paramiko
import queue


class TestConnectVPS(unittest.TestCase):

    @patch('src.vps.connect_vps.paramiko.SSHClient')
    @patch('src.vps.connect_vps.replace_placeholders')
    @patch('src.vps.connect_vps.upload_file')
    @patch('src.vps.connect_vps.execute_script')
    def test_setup_server_success(self, mock_execute, mock_upload, mock_replace, mock_ssh):
        # Setup
        mock_ssh_instance = MagicMock()
        mock_ssh.return_value = mock_ssh_instance
        mock_replace.return_value = "mocked_script_content"

        # Execute
        setup_server("192.168.1.1", "script_path", {"var": "value"}, "password")

        # Assert
        mock_ssh_instance.connect.assert_called_once_with(hostname="192.168.1.1", username="root", password="password")
        mock_replace.assert_called_once_with(script_path="script_path", replacements={"var": "value"})
        mock_upload.assert_called_once()
        mock_execute.assert_called_once_with(mock_ssh_instance, "/root/elixir.sh")
        mock_ssh_instance.close.assert_called_once()

    @patch('src.vps.connect_vps.paramiko.SSHClient')
    def test_setup_server_connection_error(self, mock_ssh):
        # Setup
        mock_ssh_instance = MagicMock()
        mock_ssh.return_value = mock_ssh_instance
        mock_ssh_instance.connect.side_effect = paramiko.SSHException("Connection failed")

        # Execute and Assert
        with self.assertRaises(VPSConnectionError):
            setup_server("192.168.1.1", "script_path", {"var": "value"}, "password")

    @patch('src.vps.connect_vps.paramiko.SSHClient')
    def test_setup_server_authentication_error(self, mock_ssh):
        # Setup
        mock_ssh_instance = MagicMock()
        mock_ssh.return_value = mock_ssh_instance
        mock_ssh_instance.connect.side_effect = paramiko.AuthenticationException("Authentication failed")

        # Execute and Assert
        with self.assertRaises(VPSAuthenticationError):
            setup_server("192.168.1.1", "script_path", {"var": "value"}, "password")

    @patch('src.vps.connect_vps.paramiko.SSHClient')
    @patch('src.vps.connect_vps.replace_placeholders')
    def test_setup_server_file_operation_error(self, mock_replace, mock_ssh):
        # Setup
        mock_ssh_instance = MagicMock()
        mock_ssh.return_value = mock_ssh_instance
        mock_replace.side_effect = FileNotFoundError("Script file not found")

        # Execute and Assert
        with self.assertRaises(VPSFileOperationError):
            setup_server("192.168.1.1", "script_path", {"var": "value"}, "password")

    @patch('src.vps.connect_vps.paramiko.SSHClient')
    @patch('src.vps.connect_vps.replace_placeholders')
    @patch('src.vps.connect_vps.upload_file')
    @patch('src.vps.connect_vps.execute_script')
    def test_setup_server_execution_error(self, mock_execute, mock_upload, mock_replace, mock_ssh):
        # Setup
        mock_ssh_instance = MagicMock()
        mock_ssh.return_value = mock_ssh_instance
        mock_replace.return_value = "mocked_script_content"
        mock_upload.return_value = None  # Simulate successful upload
        mock_execute.side_effect = Exception("Script execution failed")

        # Execute and Assert
        with self.assertRaises(VPSExecutionError):
            setup_server("192.168.1.1", "script_path", {"var": "value"}, "password")

        # Verify that all steps before execution were called
        mock_ssh_instance.connect.assert_called_once_with(hostname="192.168.1.1", username="root", password="password")
        mock_replace.assert_called_once_with(script_path="script_path", replacements={"var": "value"})
        mock_upload.assert_called_once()
        mock_execute.assert_called_once_with(mock_ssh_instance, "/root/elixir.sh")

    @patch('src.vps.connect_vps.fetch_vps_data')
    @patch('src.vps.connect_vps.setup_server')
    def test_setup_vps_success(self, mock_setup_server, mock_fetch_data):
        # Setup
        mock_fetch_data.return_value = {
            'ip': '192.168.1.1',
            'wallet': 'wallet_address',
            'project_name': 'test_project',
            'priv_key': 'private_key',
            'password': 'password'
        }

        # Execute
        result = setup_vps(1)

        # Assert
        self.assertEqual(result, {'message': 'VPS instance created, setup completed'})
        mock_fetch_data.assert_called_once_with(1)
        mock_setup_server.assert_called_once()

    @patch('src.vps.connect_vps.fetch_vps_data')
    @patch('src.vps.connect_vps.setup_server')
    def test_setup_vps_failure(self, mock_setup_server, mock_fetch_data):
        # Setup
        mock_fetch_data.return_value = {
            'ip': '192.168.1.1',
            'wallet': 'wallet_address',
            'project_name': 'test_project',
            'priv_key': 'private_key',
            'password': 'password'
        }
        mock_setup_server.side_effect = Exception("Setup failed")

        # Execute and Assert
        with self.assertRaises(VPSSetupError):
            setup_vps(1)

    @patch('src.vps.connect_vps.fetch_vps_data')
    @patch('src.vps.connect_vps.setup_server')
    def test_setup_vps_async(self, mock_setup_server, mock_fetch_data):
        # Setup
        mock_fetch_data.return_value = {
            'ip': '192.168.1.1',
            'wallet': 'wallet_address',
            'project_name': 'test_project',
            'priv_key': 'private_key',
            'password': 'password'
        }
        result_queue = queue.Queue()

        # Execute
        setup_vps_async(1, result_queue)

        # Assert
        self.assertEqual(result_queue.get(), {'message': 'VPS instance created, setup completed'})
        mock_fetch_data.assert_called_once_with(1)
        mock_setup_server.assert_called_once()

    @patch('src.vps.connect_vps.fetch_vps_data')
    @patch('src.vps.connect_vps.setup_server')
    def test_setup_vps_async_failure(self, mock_setup_server, mock_fetch_data):
        # Setup
        mock_fetch_data.return_value = {
            'ip': '192.168.1.1',
            'wallet': 'wallet_address',
            'project_name': 'test_project',
            'priv_key': 'private_key',
            'password': 'password'
        }
        mock_setup_server.side_effect = Exception("Setup failed")
        result_queue = queue.Queue()

        # Execute
        setup_vps_async(1, result_queue)

        # Assert
        self.assertIsInstance(result_queue.get(), VPSSetupError)
        mock_fetch_data.assert_called_once_with(1)
        mock_setup_server.assert_called_once()


if __name__ == '__main__':
    unittest.main()
