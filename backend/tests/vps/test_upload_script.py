import unittest
from unittest.mock import patch, MagicMock, mock_open
from paramiko import SSHException
from src.vps.upload_script import elevate_privileges, upload_file
from src.vps.vps_exceptions import VPSPrivilegeElevationError, VPSFileUploadError, VPSFileOperationError


class TestUploadScript(unittest.TestCase):

    @patch('src.vps.upload_script.time.sleep')
    def test_elevate_privileges_success(self, mock_sleep):
        # Setup
        mock_ssh_client = MagicMock()
        mock_shell = MagicMock()
        mock_ssh_client.invoke_shell.return_value = mock_shell
        mock_shell.recv.side_effect = [
            b'[sudo] password for user: ',
            b'root@hostname:~# '
        ]

        # Execute
        result = elevate_privileges(mock_ssh_client, sudo_password="password123")

        # Assert
        self.assertEqual(result, mock_shell)
        mock_shell.send.assert_any_call("sudo -i\n")
        mock_shell.send.assert_any_call("password123\n")
        mock_sleep.assert_called_with(1)

    @patch('src.vps.upload_script.time.sleep')
    def test_elevate_privileges_no_password_required(self, mock_sleep):
        # Setup
        mock_ssh_client = MagicMock()
        mock_shell = MagicMock()
        mock_ssh_client.invoke_shell.return_value = mock_shell
        mock_shell.recv.side_effect = [
            b'root@hostname:~# '
        ]

        # Execute
        result = elevate_privileges(mock_ssh_client)

        # Assert
        self.assertEqual(result, mock_shell)
        mock_shell.send.assert_called_once_with("sudo -i\n")
        mock_sleep.assert_called_with(1)

    @patch('src.vps.upload_script.time.sleep')
    def test_elevate_privileges_failure(self, mock_sleep):
        # Setup
        mock_ssh_client = MagicMock()
        mock_shell = MagicMock()
        mock_ssh_client.invoke_shell.return_value = mock_shell
        mock_shell.recv.side_effect = [
            b'[sudo] password for user: ',
            b'Sorry, try again.'
        ]

        # Execute and Assert
        with self.assertRaises(VPSPrivilegeElevationError):
            elevate_privileges(mock_ssh_client, sudo_password="wrong_password")
        mock_sleep.assert_called_with(1)

    @patch('src.vps.upload_script.elevate_privileges')
    @patch('src.vps.upload_script.time.sleep')
    @patch('builtins.open', new_callable=mock_open, read_data="script content")
    def test_upload_file_success(self, mock_file, mock_sleep, mock_elevate):
        # Setup
        mock_ssh_client = MagicMock()
        mock_sftp = MagicMock()
        mock_ssh_client.open_sftp.return_value = mock_sftp
        mock_shell = MagicMock()
        mock_elevate.return_value = mock_shell
        mock_shell.recv.return_value = b'File moved successfully'

        # Execute
        upload_file(mock_ssh_client, "/local/path/script.sh", "script.sh", "sudo_password")

        # Assert
        mock_sftp.put.assert_called_once_with("/local/path/script.sh", "/tmp/script.sh")
        mock_shell.send.assert_any_call("mv /tmp/script.sh /root/script.sh\n")
        mock_shell.send.assert_any_call("chmod +x /root/script.sh\n")
        mock_sleep.assert_called_with(1)
        mock_file.assert_called_once_with("/local/path/script.sh", "r")

    @patch('src.vps.upload_script.elevate_privileges')
    @patch('src.vps.upload_script.time.sleep')
    def test_upload_file_sftp_error(self, mock_sleep, mock_elevate):
        # Setup
        mock_ssh_client = MagicMock()
        mock_ssh_client.open_sftp.side_effect = SSHException("SFTP error")

        # Execute and Assert
        with self.assertRaises(VPSFileUploadError):
            upload_file(mock_ssh_client, "/local/path/script.sh", "script.sh", "sudo_password")
        mock_sleep.assert_not_called()

    @patch('src.vps.upload_script.elevate_privileges')
    @patch('src.vps.upload_script.time.sleep')
    @patch('builtins.open', new_callable=mock_open, read_data="script content")
    def test_upload_file_move_error(self, mock_file, mock_sleep, mock_elevate):
        # Setup
        mock_ssh_client = MagicMock()
        mock_sftp = MagicMock()
        mock_ssh_client.open_sftp.return_value = mock_sftp
        mock_shell = MagicMock()
        mock_elevate.return_value = mock_shell
        mock_shell.recv.return_value = b'mv: cannot move'

        # Execute and Assert
        with self.assertRaises(VPSFileOperationError):
            upload_file(mock_ssh_client, "/local/path/script.sh", "script.sh", "sudo_password")
        mock_sleep.assert_called_with(1)
        mock_file.assert_called_once_with("/local/path/script.sh", "r")

    @patch('src.vps.upload_script.elevate_privileges')
    @patch('src.vps.upload_script.time.sleep')
    @patch('builtins.open', new_callable=mock_open, read_data="script content")
    @patch('os.remove')
    def test_upload_file_local_delete(self, mock_remove, mock_file, mock_sleep, mock_elevate):
        # Setup
        mock_ssh_client = MagicMock()
        mock_sftp = MagicMock()
        mock_ssh_client.open_sftp.return_value = mock_sftp
        mock_shell = MagicMock()
        mock_elevate.return_value = mock_shell
        mock_shell.recv.return_value = b'File moved successfully'

        # Execute
        upload_file(mock_ssh_client, "/local/path/script.sh", "script.sh", "sudo_password")

        # Assert
        mock_remove.assert_called_once_with("/local/path/script.sh")
        mock_sleep.assert_called_with(1)
        mock_file.assert_called_once_with("/local/path/script.sh", "r")


if __name__ == '__main__':
    unittest.main()
