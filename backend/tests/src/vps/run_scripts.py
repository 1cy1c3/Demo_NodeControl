import re


def execute_script(ssh_client, script_path):
    """
    Executes a shell script located at script_path on the remote server.

    :param ssh_client: An active SSH client connected to the remote server
    :param script_path: Path to the shell script to execute on the remote server
    """
    try:
        # Execute the script on the remote server
        ssh_client.exec_command(f"sudo bash {script_path}")
        # Capt ure output and errors
    except Exception as e:
        print(f"Failed to execute script. Error: {e}")


def replace_placeholders(script_path, replacements):
    """
    Replace placeholders in the script content with provided values,
    preserving "0x" prefix for hexadecimal values and handling strings without quotes.

    :param script_path: The original script path for the templates
    :param replacements: A dictionary of placeholder-value pairs
    :return: The script content with placeholders replaced
    """
    with open(script_path, 'r') as f:
        script_content = f.read()

    def replacement_func(match):
        placeholder = match.group(1)
        if placeholder in replacements:
            value = replacements[placeholder]
            return str(value).strip("'\"")
        return match.group(0)  # Return original if no replacement found

    # Use regex to find placeholders and apply the replacement function
    return re.sub(r'\{(\w+)}', replacement_func, script_content)


if __name__ == "__main__":
    # pem_file_path = '../contabo/my-ec2-keypair-test-.pem'  # Replace with the path to your .pem file

    instance_ip = '185.229.65.119'  # Replace with your EC2 instance's public IP
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

    temp = replace_placeholders(script_path='../../scripts/templates/elixir.sh', replacements=package)
    print(temp)
