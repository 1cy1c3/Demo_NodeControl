import logging
import time
import os
from typing import Optional
from paramiko import SSHClient, Channel
from tenacity import retry, stop_after_attempt, wait_exponential

from src.vps.vps_exceptions import (
    VPSPrivilegeElevationError,
    VPSFileUploadError,
    VPSFileOperationError
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def elevate_privileges(ssh_client: SSHClient, sudo_password: Optional[str] = None) -> Channel:
    """
    Elevates privileges to root on the remote server.

    :param ssh_client: An active SSH client connected to the remote server
    :param sudo_password: Password for sudo (if required)
    :return: Shell channel with elevated privileges
    :raises VPSPrivilegeElevationError: If there's an error elevating privileges
    """
    try:
        print("Step 1")
        shell = ssh_client.invoke_shell()
        shell.send("sudo -i\n")
        print("Step 2")

        time.sleep(1)

        output = shell.recv(1024).decode('utf-8')
        print("Step 3")

        if "[sudo] password" in output:
            print("Step 1")

            if sudo_password is None:
                print("Step 1")

                raise ValueError("Sudo password required but not provided")
            shell.send(f"{sudo_password}\n")
            time.sleep(1)
        print("Step 4")

        output = shell.recv(1024).decode('utf-8')
        print(output)
        if "root@" in output:
            logger.info("Successfully elevated privileges to root")
            return shell
        else:
            raise VPSPrivilegeElevationError("Failed to elevate privileges")
    except Exception as e:
        logger.error(f"Error during privilege elevation: {e}")
        raise VPSPrivilegeElevationError(f"Error during privilege elevation: {str(e)}") from e


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def upload_file(ssh_client: SSHClient, local_file_path: str, filename: str, sudo_password: Optional[str] = None) -> None:
    """
    Uploads a local file to the remote server and moves it to /root/ with elevated privileges.

    :param ssh_client: An active SSH client connected to the remote server
    :param local_file_path: Path to the local file to upload
    :param filename: Destination filename on the remote server
    :param sudo_password: Password for sudo (if required)
    :raises VPSFileUploadError: If there's an error uploading the file
    :raises VPSFileOperationError: If there's an error moving or changing permissions of the file
    """
    temp_path = f"/tmp/{filename}"
    final_path = f"/root/{filename}"

    try:
        shell = elevate_privileges(ssh_client, sudo_password)

        sftp = ssh_client.open_sftp()
        logger.info(f"Attempting to upload {local_file_path} to {temp_path}")
        sftp.put(local_file_path, temp_path)
        sftp.close()
        logger.info(f"File uploaded successfully to {temp_path}")

        move_str = f"mv {temp_path} {final_path}\n"
        shell.send(move_str.encode('utf-8'))
        time.sleep(1)
        output = shell.recv(1024).decode('utf-8')
        if "mv: cannot move" in output:
            raise VPSFileOperationError(f"Failed to move file: {output}")

        logger.info(f"File successfully moved to {final_path}")
        shell.send(f"chmod +x {final_path}\n".encode('utf-8'))
        time.sleep(1)
        output = shell.recv(1024).decode('utf-8')
        logger.info(f"Changed file permissions: {output}")

        os.remove(local_file_path)
        logger.info(f"Local file {local_file_path} deleted successfully")

    except VPSPrivilegeElevationError as e:
        logger.error(f"Failed to elevate privileges: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to upload and move file. Error: {e}")
        raise VPSFileUploadError(f"Failed to upload and move file: {str(e)}") from e


if __name__ == "__main__":
    # Test code
    from paramiko import SSHClient, AutoAddPolicy

    ssh = SSHClient()
    try:

        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.connect('example.com', username='user', password='password')

        upload_file(ssh, '/path/to/local/file.sh', 'remote_file.sh', 'sudo_password')
        logger.info("File upload test completed successfully")
    except (VPSPrivilegeElevationError, VPSFileUploadError, VPSFileOperationError) as e:
        logger.error(f"Error during file upload test: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during file upload test: {e}")
    finally:
        ssh.close()
