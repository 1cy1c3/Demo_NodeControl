import time
import paramiko
import logging
import queue
import threading
import uuid

from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

from src.database.database import fetch_vps_data
from src.vps.run_scripts import execute_script, replace_placeholders, stream_logs
from src.vps.upload_script import upload_file
from src.vps.vps_exceptions import (
    VPSConnectionError, VPSAuthenticationError, VPSFileOperationError,
    VPSSetupError, VPSExecutionError
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def vps_logs_stream(instanceIp: str, password: str = "", username='root', pem=False):
    ssh = None
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        logger.info(f"Attempting to connect to {instanceIp}")
        if not pem:
            ssh.connect(hostname=instanceIp, username=username, password=password)
        else:
            ssh.connect(hostname=instanceIp, username="ubuntu", key_filename="src/aws/default.pem")

        logger.info(f"Successfully connected to {instanceIp}")

        logger.info("Starting to stream logs")
        log_count = 0
        for log_line in stream_logs(ssh):
            print(f"vps_logs_stream yielding: {log_line}")  # Debug-Ausgabe
            yield log_line
            log_count += 1
        logger.info(f"Finished streaming logs. Total lines: {log_count}")

    except paramiko.AuthenticationException as auth_error:
        logger.error(f"Authentication failed: {auth_error}")
        yield f"Error: Authentication failed. {str(auth_error)}"
    except paramiko.SSHException as ssh_error:
        logger.error(f"SSH connection error: {ssh_error}")
        yield f"Error: SSH connection failed. {str(ssh_error)}"
    except Exception as e:
        logger.error(f"Failed to stream logs {instanceIp}. Error: {e}")
        yield f"Error: Failed to stream logs. {str(e)}"
    finally:
        if ssh:
            ssh.close()
            print("SSH connection closed.")  # Debug-Ausgabe


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def setup_server(instanceIp: str, script_path: str, payload: Dict[str, Any], password: str, username='root', pem=False) -> None:
    """
    Connects to a VPS instance and executes a setup script.
    :param pem: Bool to set login method
    :param instanceIp: Public IP address of the VPS instance
    :param script_path: Path to script templates
    :param payload: Variables to exchange in Scripts
    :param password: Instance Password
    :param username: Username for the VPS instance (default: 'root')
    :raises VPSConnectionError: If there's an error connecting to the VPS
    :raises VPSAuthenticationError: If authentication fails
    :raises VPSFileOperationError: If there's an error with file operations
    :raises VPSExecutionError: If there's an error executing the script
    """

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        logger.info(f"Attempting to connect to {instanceIp}")
        if not pem:
            ssh.connect(hostname=instanceIp, username=username, password=password)
        else:
            ssh.connect(hostname=instanceIp, username="ubuntu", key_filename="src/aws/default.pem")

        logger.info(f"Connected to {instanceIp}")

        setup_file = replace_placeholders(script_path=script_path, replacements=payload)
        file_path = f'scripts/elixir/'
        file_name = f'elixir-{uuid.uuid4()}.sh'

        with open(file_path + file_name, 'w', newline='\n') as file:
            file.write(setup_file)
        logger.info("Setup File Saved")

        time.sleep(60)  # Wait for instance initialization

        upload_file(ssh, local_file_path=file_path + file_name, filename='elixir.sh')
        logger.info("File Uploaded")

        time.sleep(60)

        try:
            execute_script(ssh, "/root/elixir.sh")
            logger.info("File Executed Successfully")
        except Exception as exec_error:
            logger.error(f"Error executing script: {exec_error}")
            raise VPSExecutionError(f"Failed to execute script on {instanceIp}: {str(exec_error)}") from exec_error

        logger.info("File Executed")

        time.sleep(60)
        ssh.close()
        logger.info("Session Closed")

    except paramiko.AuthenticationException as auth_error:
        logger.error(f"Authentication failed: {auth_error}")
        raise VPSAuthenticationError(f"Failed to authenticate with {instanceIp}: {str(auth_error)}") from auth_error
    except paramiko.SSHException as ssh_error:
        logger.error(f"SSH connection error: {ssh_error}")
        raise VPSConnectionError(
            f"Failed to establish SSH connection with {instanceIp}: {str(ssh_error)}") from ssh_error
    except FileNotFoundError as fnf_error:
        logger.error(f"File not found: {fnf_error}")
        raise VPSFileOperationError(f"File operation error: {str(fnf_error)}") from fnf_error
    except Exception as e:
        logger.error(f"Failed to setup server {instanceIp}. Error: {e}")
        raise VPSSetupError(f"Failed to setup server {instanceIp}: {str(e)}") from e


def setup_vps(user_project_id: int) -> Dict[str, Any]:
    """
    Set up a VPS instance.

    :param user_project_id: ID of the user project
    :return: Dictionary containing setup result
    :raises VPSSetupError: If there's an error during VPS setup
    """
    try:
        result_queue = queue.Queue()

        thread = threading.Thread(
            target=setup_vps_async,
            args=(user_project_id, result_queue)
        )
        thread.start()
        thread.join()

        result = result_queue.get()

        if isinstance(result, Exception):
            raise result

        return result
    except queue.Empty:
        logger.error("Setup process timed out")
        raise VPSSetupError("VPS setup process timed out")
    except Exception as e:
        logger.error(f"Error setting up VPS: {e}")
        raise VPSSetupError(f"Failed to set up VPS: {str(e)}") from e


def setup_vps_async(user_project_id: int, result_queue: queue.Queue) -> None:
    """
    Asynchronously set up a VPS instance.

    :param user_project_id: ID of the user project
    :param result_queue: Queue to put the result of the setup process
    """
    try:
        data = fetch_vps_data(user_project_id)
        ip_address = data.get('ip')
        wallet = data.get('wallet')
        project_name = data.get('project_name')
        private_key = data.get('priv_key')
        password = data.get('password')

        payload = {
            'ip': ip_address,
            'name': "1cy1c3",
            'wallet': wallet,
            'priv_key': private_key,
        }

        setup_server(instanceIp=ip_address, script_path=f"scripts/templates/{project_name}.sh",
                     payload=payload, password=password, username='root', pem=True)  # TODO: True for MVP, change later

        result_queue.put({'message': 'VPS instance created, setup completed'})
    except Exception as e:
        logger.error(f"VPS setup failed: {e}")
        result_queue.put(VPSSetupError(f"VPS setup failed: {str(e)}"))


if __name__ == "__main__":
    # Test code remains unchanged
    pass
