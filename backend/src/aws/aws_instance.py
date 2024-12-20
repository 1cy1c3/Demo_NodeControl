import os
import time
import boto3
import base64
import logging

from typing import Dict, Any
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from tenacity import retry, stop_after_attempt, wait_exponential

from src.database.database import (generate_password_and_key, create_user_project, save_encrypted_password,
                                   update_instance_ip)


# Load Env Vars
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
SECURITY_GROUP_ID = os.getenv('SECURITY_GROUP_ID')

# EC2 instance parameters
INSTANCE_TYPE: str = "t2.micro"
AMI_ID: str = "ami-0e04bcbe83a83792e"  # Amazon Linux 2 AMI (HVM), SSD Volume Type
KEY_PAIR_NAME: str = "default"
ROOT_PASSWORD: str = "12345678"
AWS_REGION: str = "eu-central-1"

logger = logging.getLogger(__name__)


class AWSInstanceDeletionError(Exception):
    """Custom exception for AWS instance deletion errors."""
    pass


class AWSInstanceCreationError(Exception):
    """Custom exception for AWS instance creation errors."""
    pass


def get_root_access() -> str:
    user_data_script = f"""#!/bin/bash
                            echo 'root:{ROOT_PASSWORD}' | chpasswd
                            sed -i 's/^#PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
                            sed -i 's/^#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
                            systemctl restart sshd"""
    return base64.b64encode(user_data_script.encode('ascii')).decode('ascii')


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def create_ec2_instance(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a new EC2 instance with improved error handling.

    :param data: Dictionary containing instance creation parameters
    :return: Dictionary containing instance_id and public_ip
    :raises AWSInstanceCreationError: If there's an error during instance creation
    """
    try:
        project_id = data.get('project_id')
        user_id = data.get('user_id')

        password, iv_key = generate_password_and_key()
        if not password:
            raise AWSInstanceCreationError("Failed to generate password")

        ec2 = boto3.client('ec2',
                           aws_access_key_id=AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                           region_name=data.get('region', AWS_REGION))

        response = ec2.run_instances(
            ImageId=data.get('image_id', AMI_ID),
            InstanceType=data.get('instance_type', INSTANCE_TYPE),
            SecurityGroupIds=[data.get('security_group_id', SECURITY_GROUP_ID)],
            KeyName=data.get('key_pair_name', KEY_PAIR_NAME),
            MinCount=1,
            MaxCount=1,
            # UserData=get_user_data()  # TODO: Keep like this for MVP
        )

        instance_id: str = response['Instances'][0]['InstanceId']
        logger.info(f"EC2 instance {instance_id} has been created.")

        if not wait_for_instance_running(instance_id):
            raise AWSInstanceCreationError(
                f"Instance {instance_id} did not enter 'running' state in the expected time.")

        public_ip = get_public_ip(instance_id)
        if not public_ip:
            raise AWSInstanceCreationError(f"Failed to retrieve public IP for instance {instance_id}")

        user_project_id = create_user_project(user_id=user_id, project_id=project_id, instance_id=instance_id)

        if not user_project_id:
            raise AWSInstanceCreationError(f"Failed creating user project for instance ID {instance_id}")

        if not save_encrypted_password(user_project_id=user_project_id, password=password, fernet_key=iv_key):
            raise AWSInstanceCreationError(f"Failed saving password for instance ID {instance_id}")

        logger.info(f"Instance created successfully with ID: {instance_id} and project ID: {user_project_id}")
        if not update_instance_ip(instance_id, public_ip):
            raise AWSInstanceCreationError(f"Failed to save Public IP for instance ID {instance_id}")

        return {
            "user_project_id": user_project_id,
            "instance_id": instance_id,
            "public_ip": public_ip
        }

    except ClientError as e:
        logger.error(f"Error creating AWS EC2 instance: {e}")
        raise AWSInstanceCreationError(f"Failed to create AWS EC2 instance: {e}") from e
    except KeyError as e:
        logger.error(f"Unexpected response format from AWS API: {e}")
        raise AWSInstanceCreationError(f"Unexpected response format from AWS API: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error during AWS EC2 instance creation: {e}")
        raise AWSInstanceCreationError(f"Unexpected error during AWS EC2 instance creation: {e}") from e


def wait_for_instance_running(instance_id: str, max_retries: int = 60, delay: int = 15) -> bool:
    logger.info("Waiting for instance to enter 'running' state...")
    for i in range(max_retries):
        try:
            state = get_instance_status(instance_id)
            logger.info(f"Current state: {state}")

            if state == 'running':
                logger.info("Instance is now running!")
                return True

            if state == 'terminated' or state == 'shutting-down':
                logger.error(f"Instance entered {state} state. Something went wrong.")
                return False

            time.sleep(delay)
        except ClientError as e:
            logger.error(f"Error checking instance state: {e}")
            return False

    logger.warning(f"Timed out after {max_retries * delay} seconds. Instance may still be initializing.")
    return False


def get_instance_status(instance_id: str) -> str:
    ec2 = boto3.client('ec2', aws_access_key_id=AWS_ACCESS_KEY_ID,
                       aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                       region_name=AWS_REGION)
    response = ec2.describe_instances(InstanceIds=[instance_id])
    state = response['Reservations'][0]['Instances'][0]['State']['Name']
    return state


def get_public_ip(instance_id: str) -> str:
    ec2 = boto3.resource('ec2', aws_access_key_id=AWS_ACCESS_KEY_ID,
                         aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                         region_name=AWS_REGION)
    instance = ec2.Instance(instance_id)
    return instance.public_ip_address


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def delete_ec2_instance(instance_id: str) -> bool:
    """
    Deletes a specific EC2 instance by its instance ID.

    :param instance_id: The ID of the EC2 instance to delete
    :return: True if the instance was successfully deleted, False otherwise
    :raises AWSInstanceDeletionError: If there's an error during instance deletion
    """
    try:
        ec2 = boto3.client('ec2',
                           aws_access_key_id=AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                           region_name=AWS_REGION)

        # Terminate the instance
        response = ec2.terminate_instances(InstanceIds=[instance_id])

        terminating_instances = response['TerminatingInstances']
        if not terminating_instances:
            raise AWSInstanceDeletionError(f"No instance found with ID: {instance_id}")

        current_state = terminating_instances[0]['CurrentState']['Name']
        logger.info(f"Instance {instance_id} state changed to: {current_state}")

        # Wait for the instance to be terminated
        waiter = ec2.get_waiter('instance_terminated')
        waiter.wait(InstanceIds=[instance_id])

        logger.info(f"EC2 instance {instance_id} has been successfully terminated.")
        return True

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"Error deleting AWS EC2 instance: {error_code} - {error_message}")
        raise AWSInstanceDeletionError(f"Failed to delete AWS EC2 instance: {error_message}") from e
    except Exception as e:
        logger.error(f"Unexpected error during AWS EC2 instance deletion: {str(e)}")
        raise AWSInstanceDeletionError(f"Unexpected error during AWS EC2 instance deletion: {str(e)}") from e
