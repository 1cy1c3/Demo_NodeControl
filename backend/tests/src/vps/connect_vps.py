import time
import json
import paramiko
import logging
import queue
import threading

from random import randint
from src.database.database import fetch_vps_data
from src.vps.run_scripts import execute_script, replace_placeholders
from src.vps.upload_script import upload_file


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_server(instanceIp: str, script_path: str,  replacement_vars: dict, password: str, username='root'):
    """
    Connects to an EC2 instance and executes a command.

    :param password: Instance Password
    :param replacement_vars: Variables to exchange in Scripts
    :param script_path: Path to script templates
    :param instanceIp: Public IP address of the EC2 instance
    :param username: Username for the EC2 instance (default: 'vps' for Ubuntu)
    """

    time.sleep(60)  # Give the Instance a minute to initialize before connecting

    try:
        # Create a new SSH client instance
        ssh = paramiko.SSHClient()

        # Automatically add the server's host key (not recommended for production)
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Load the private key to connect ot the instance
        ssh.connect(hostname=instanceIp, username=username, password=password)

        # load password and username to connect to the instance
        # ssh.connect(hostname=instanceIp, username='root', password=password)

        print(f"Connected to {instanceIp}")
        setup_file = replace_placeholders(script_path=script_path, replacements=replacement_vars)
        file_path = f'scripts/elixir/'
        file_name = f'elixir-{randint(1, 10000)}.sh'

        with open(file_path + file_name, 'w', newline='\n') as file:
            file.write(setup_file)  # Write the content to the file

        print("Setup File Saved")
        time.sleep(60)  # Give the Instance a minute to initialize before connecting

        upload_file(ssh, local_file_path=file_path + file_name, filename='elixir.sh')
        print("File Uploaded")

        time.sleep(60)

        execute_script(ssh, "/root/elixir.sh")
        print("File Executed")

        # Close the SSH connection
        time.sleep(60)
        ssh.close()
        print("Session Closed")

    except paramiko.AuthenticationException as auth_error:
        print(f"Authentication failed: {auth_error}")
    except paramiko.SSHException as ssh_error:
        print(f"SSH connection error: {ssh_error}")
    except FileNotFoundError as fnf_error:
        print(f"File not found: {fnf_error}")
    except Exception as e:
        print(f"Failed to connect to {instanceIp}. Error: {e}")


def setup_vps(user_project_id: int) -> int:
    # Create a queue to get the result from the thread
    result_queue = queue.Queue()

    # Start the setup process in a new thread
    thread = threading.Thread(
        target=setup_vps_async,
        args=(user_project_id, result_queue)
    )
    thread.start()

    # Wait for the thread to finish and get the result
    thread.join()
    result = result_queue.get()

    return result


def setup_vps_async(user_project_id: int) -> json:
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

        setup_server(instanceIp=ip_address, script_path=f"scripts/templates/{project_name}.sh", replacement_vars=payload,
                     password=password, username='root')

        return {
            'message': 'AWS instance created, setup ended'
        }, 202  # 202 Accepted

    except Exception as e:
        # Log the exception or handle it appropriately
        logger.error(f"VPS creation failed after retries: {e}")
        return {'error': str(e)}, 500


if __name__ == "__main__":
    pem_file_path = '../contabo/my-ec2-keypair-test-.pem'

    instance_ip = ''  # Replace with your EC2 instance's public IP
    password = ''
    wallet = ''
    private_key = ''
    validator_name = ''

    package = {
        'ip': instance_ip,
        'name': validator_name,
        'wallet': wallet,
        'priv_key': private_key,
    }

    setup_server(instance_ip, script_path="scripts/templates/elixir.sh", password=password, replacement_vars=package)
