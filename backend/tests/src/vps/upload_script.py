import logging
import time


# Ensure logging is configured
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def elevate_privileges(ssh_client, sudo_password=None):
    try:
        shell = ssh_client.invoke_shell()
        shell.send("sudo -i\n")
        time.sleep(1)

        output = shell.recv(1024).decode('utf-8')
        if "[sudo] password" in output:
            if sudo_password is None:
                raise ValueError("Sudo password required but not provided")
            shell.send(f"{sudo_password}\n")
            time.sleep(1)

        output = shell.recv(1024).decode('utf-8')
        if "root@" in output:
            logging.info("Successfully elevated privileges to root")
            return shell
        else:
            logging.error("Failed to elevate privileges")
            return None
    except Exception as e:
        logging.error(f"Error during privilege elevation: {e}")
        return None


def upload_file(ssh_client, local_file_path, filename, sudo_password=None):
    """
    Uploads a local file to the remote server and moves it to /root/ with elevated privileges.

    :param ssh_client: An active SSH client connected to the remote server
    :param local_file_path: Path to the local file to upload
    :param filename: Destination filename on the remote server
    :param sudo_password: Password for sudo (if required)
    """
    temp_path = f"/tmp/{filename}"
    final_path = f"/root/{filename}"

    try:
        # Upload file to /tmp first
        shell = elevate_privileges(ssh_client, sudo_password)
        if not shell:
            raise Exception("Failed to elevate privileges")

        sftp = ssh_client.open_sftp()
        logging.info(f"Attempting to upload {local_file_path} to {temp_path}")
        sftp.put(local_file_path, temp_path)
        sftp.close()
        logging.info(f"File uploaded successfully to {temp_path}")

        # Move file from /tmp to /root
        print(f"mv {temp_path} {final_path}\n")
        shell.send(f"mv {temp_path} {final_path}\n")

        output = shell.recv(1024).decode('utf-8')
        if "mv: cannot move" in output:
            raise Exception(f"Failed to move file: {output}")

        logging.info(f"File successfully moved to {final_path}")
        shell.send(f"sudo chmod +x {filename}\n")
        output = shell.recv(1024).decode('utf-8')
        logging.info(f"{output}")

    except Exception as e:
        logging.error(f"Failed to upload and move file. Error: {e}")
