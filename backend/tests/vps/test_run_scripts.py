import unittest
from unittest.mock import patch, MagicMock
from src.vps.run_scripts import execute_script, replace_placeholders
from src.vps.vps_exceptions import VPSExecutionError, VPSFileOperationError


class TestRunScripts(unittest.TestCase):

    @patch('src.vps.run_scripts.logger')
    def test_execute_script_success(self, mock_logger):
        # Setup
        mock_ssh_client = MagicMock()
        mock_channel = MagicMock()
        mock_channel.recv_exit_status.return_value = 0
        mock_ssh_client.exec_command.return_value = (None, mock_channel, None)

        # Execute
        execute_script(mock_ssh_client, "/path/to/script.sh")

        # Assert
        mock_ssh_client.exec_command.assert_called_once_with("sudo bash /path/to/script.sh")
        mock_logger.info.assert_called_with("Script executed successfully")

    @patch('src.vps.run_scripts.logger')
    def test_execute_script_failure(self, mock_logger):
        # Setup
        mock_ssh_client = MagicMock()
        mock_channel = MagicMock()
        mock_channel.recv_exit_status.return_value = 1
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b"Error executing script"
        mock_ssh_client.exec_command.return_value = (None, mock_channel, mock_stderr)

        # Execute and Assert
        with self.assertRaises(VPSExecutionError):
            execute_script(mock_ssh_client, "/path/to/script.sh")

        mock_logger.error.assert_called_with("Script execution failed with exit status 1. Error: Error executing script")

    @patch('src.vps.run_scripts.logger')
    def test_execute_script_exception(self, mock_logger):
        # Setup
        mock_ssh_client = MagicMock()
        mock_ssh_client.exec_command.side_effect = Exception("SSH error")

        # Execute and Assert
        with self.assertRaises(VPSExecutionError):
            execute_script(mock_ssh_client, "/path/to/script.sh")

        mock_logger.error.assert_called_with("Failed to execute script. Error: SSH error")

    def test_replace_placeholders_success(self):
        # Setup
        script_content = "Hello {name}, your balance is {balance}"
        replacements = {"name": "Alice", "balance": "100 ETH"}

        # Execute
        result = replace_placeholders(script_content, replacements)

        # Assert
        self.assertEqual(result, "Hello Alice, your balance is 100 ETH")

    def test_replace_placeholders_missing_placeholder(self):
        # Setup
        script_content = "Hello {name}, your balance is {balance}"
        replacements = {"name": "Alice"}

        # Execute
        result = replace_placeholders(script_content, replacements)

        # Assert
        self.assertEqual(result, "Hello Alice, your balance is {balance}")

    @patch('src.vps.run_scripts.logger')
    def test_replace_placeholders_file_not_found(self, mock_logger):
        # Setup
        script_path = "/non/existent/path.sh"
        replacements = {"name": "Alice"}

        # Execute and Assert
        with self.assertRaises(VPSFileOperationError):
            replace_placeholders(script_path, replacements)

        mock_logger.error.assert_called_with(f"Script file not found: {script_path}")

    @patch('builtins.open', new_callable=MagicMock)
    @patch('src.vps.run_scripts.logger')
    def test_replace_placeholders_read_error(self, mock_logger, mock_open):
        # Setup
        script_path = "/path/to/script.sh"
        replacements = {"name": "Alice"}
        mock_open.side_effect = IOError("Read error")

        # Execute and Assert
        with self.assertRaises(VPSFileOperationError):
            replace_placeholders(script_path, replacements)

        mock_logger.error.assert_called_with(f"Error replacing placeholders in script: Read error")


if __name__ == '__main__':
    unittest.main()