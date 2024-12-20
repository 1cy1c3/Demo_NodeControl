import re
import time
import signal
import logging
from typing import Dict, Any, Generator
from paramiko import SSHClient
from tenacity import retry, stop_after_attempt, wait_exponential

from src.vps.vps_exceptions import VPSExecutionError, VPSFileOperationError
# from src.vps.upload_script import elevate_privileges

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def execute_script(ssh_client: SSHClient, script_path: str) -> None:
    """
    Executes a shell script located at script_path on the remote server.

    :param ssh_client: An active SSH client connected to the remote server
    :param script_path: Path to the shell script to execute on the remote server
    :raises VPSExecutionError: If there's an error executing the script
    """
    try:
        logger.info(f"Executing script: {script_path}")
        stdin, stdout, stderr = ssh_client.exec_command(f"sudo bash {script_path}")

        # Read and log output in real-time
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                line = read_vps_line(stdout)
                logger.info(line)

        # Get the exit status
        exit_status = stdout.channel.recv_exit_status()

        if exit_status != 0:
            error_output = stderr.read().decode('utf-8')
            logger.error(f"Script execution failed with exit status {exit_status}. Error: {error_output}")
            raise VPSExecutionError(f"Script execution failed: {error_output}")

        logger.info("Script executed successfully")
    except Exception as e:
        logger.error(f"Failed to execute script. Error: {e}")
        raise VPSExecutionError(f"Failed to execute script: {str(e)}") from e


def read_vps_line(stdout):
    return stdout.channel.recv(1024).decode('utf-8').strip()


def stream_logs(ssh_client: SSHClient) -> Generator[str, None, None]:
    stdin, stdout, stderr = [None] * 3
    try:
        logger.info("Starting log streaming...")
        stdin, stdout, stderr = ssh_client.exec_command("sudo docker logs -f elixir --tail 10", get_pty=True)

        while not stdout.channel.closed:
            line = stdout.readline()
            if line:
                stripped_line = line.strip()
                if stripped_line:
                    logger.info(f"Log line: {stripped_line}")
                    yield stripped_line
            else:
                time.sleep(0.1)  # Short sleep to prevent CPU overuse
    except Exception as e:
        logger.error(f"Failed to execute command. Error: {e}")
        yield f"Error: Failed to execute command. {str(e)}"
    finally:
        logger.info("Cleaning up SSH resources")
        if stdout:
            stdout.close()
        if stdin:
            stdin.close()
        if stderr:
            stderr.close()


def replace_placeholders(script_path: str, replacements: Dict[str, Any]) -> str:
    """
    Replace placeholders in the script content with provided values,
    preserving "0x" prefix for hexadecimal values and handling strings without quotes.

    :param script_path: The original script path for the templates
    :param replacements: A dictionary of placeholder-value pairs
    :return: The script content with placeholders replaced
    :raises VPSFileOperationError: If there's an error reading the script file
    """
    try:
        with open(script_path, 'r') as f:
            script_content = f.read()

        def replacement_func(match):
            placeholder = match.group(1)
            if placeholder in replacements:
                value = replacements[placeholder]
                return str(value).strip("'\"")
            return match.group(0)  # Return original if no replacement found

        # Use regex to find placeholders and apply the replacement function
        replaced_content = re.sub(r'\{(\w+)}', replacement_func, script_content)
        logger.info(f"Placeholders replaced in script: {script_path}")
        return replaced_content
    except FileNotFoundError:
        logger.error(f"Script file not found: {script_path}")
        raise VPSFileOperationError(f"Script file not found: {script_path}")
    except Exception as e:
        logger.error(f"Error replacing placeholders in script: {e}")
        raise VPSFileOperationError(f"Error replacing placeholders in script: {str(e)}") from e


if __name__ == "__main__":
    # Test code
    instance_ip = '185.229.65.119'
    password = 'szJ6WwYHa0iJ'
    wallet = '0x6D8511196F3aFBE45147A745A39caD977aF3D454'
    private_key = '0xa98ebb7f43e479c5459159caa98bc67c6881f91565d491c941dbf2a9fdd4e567'
    validator_name = '1cy1c3.eth'

    package = {
        'ip': instance_ip,
        'name': validator_name,
        'wallet': wallet,
        'priv_key': private_key,
    }

    try:
        temp = replace_placeholders(script_path='../../scripts/templates/elixir.sh', replacements=package)
        print(temp)
    except VPSFileOperationError as e:
        logger.error(f"Error in replace_placeholders: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
