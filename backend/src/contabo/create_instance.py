import os
import threading
import requests
import uuid
import logging
import time
import queue

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from src.aws.aws_instance import create_ec2_instance
from src.database.database import (
    update_instance_ip, generate_password_and_key, save_encrypted_password, create_user_project
)
from src.contabo.contabo_exceptions import (
    ContaboAuthError, ContaboInstanceCreationError, InstanceSetupError, InstanceCancellationError,
    InstanceStatusCheckError, SetupInstanceError
)


load_dotenv()
APP_SECRET = os.getenv('APP_SECRET')
CONTABO_CLIENT_ID = os.getenv('CONTABO_CLIENT_ID')
CONTABO_CLIENT_SECRET = os.getenv('CONTABO_CLIENT_SECRET')
CONTABO_API_USER = os.getenv('CONTABO_API_USER')
CONTABO_API_SECRET = os.getenv('CONTABO_API_SECRET')
CONTABO_API_AUTH = os.getenv('CONTABO_API_AUTH')
CONTABO_API_COMPUTE_INSTANCE = os.getenv('CONTABO_API_COMPUTE_INSTANCE')

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_access_token() -> str:
    headers = {
        'client_id': CONTABO_CLIENT_ID,
        'client_secret': CONTABO_CLIENT_SECRET,
        'username': CONTABO_API_USER,
        'password': CONTABO_API_SECRET,
        'grant_type': 'password'
    }

    try:
        response = requests.post(CONTABO_API_AUTH, headers=headers)
        response.raise_for_status()
        print(response)
        token_data = response.json()
        if 'access_token' not in token_data:
            raise ContaboAuthError("Access token not found in response")

        return token_data['access_token']
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during Contabo API authentication: {e}")
        raise ContaboAuthError(f"Failed to authenticate with Contabo API: {e}") from e
    except ValueError as e:
        logger.error(f"Error parsing Contabo API response: {e}")
        raise ContaboAuthError(f"Failed to parse Contabo API response: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error during Contabo API authentication: {e}")
        raise ContaboAuthError(f"Unexpected error during Contabo API authentication: {e}") from e


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def create_instance(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a new VPS instance with retry mechanism and improved error handling.

    :param data: Dictionary containing instance creation parameters
    :return: Dictionary containing user_project_id and instance_id
    :raises ContaboInstanceCreationError: If there's an error during instance creation
    """
    try:
        image_id = data.get('imageId')
        product_id = data.get('productId')
        region = data.get('region', 'EU')
        period = data.get('period', 1)
        display_name = data.get('displayName')
        default_user = data.get('defaultUser', 'root')
        project_id = data.get('project_id')
        user_id = data.get('user_id')

        password, iv_key = generate_password_and_key()
        if not password:
            raise ContaboInstanceCreationError("Failed to generate password")

        ACCESS_TOKEN = get_access_token()
        if not ACCESS_TOKEN:
            raise ContaboInstanceCreationError("Failed to get access token")

        payload = {
            "imageId": image_id,
            "productId": product_id,
            "region": region,
            "rootPassword": password,
            "period": period,
            "displayName": display_name,
            "defaultUser": default_user,
            "addOns": {
                "privateNetworking": {},
                "additionalIps": {},
                "extraStorage": {},
                "customImage": {}
            },
            "applicationId": image_id
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'x-request-id': str(uuid.uuid4()),
            'x-trace-id': str(uuid.uuid4())[:6]
        }

        response = requests.post(CONTABO_API_COMPUTE_INSTANCE, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        response_data = response.json()

        instance_id = response_data['data'][0]['instanceId']
        user_project_id = create_user_project(user_id=user_id, project_id=project_id, instance_id=instance_id)

        if not user_project_id:
            raise ContaboInstanceCreationError(f"Failed creating user project for instance ID {instance_id}")

        if not save_encrypted_password(user_project_id=user_project_id, password=password, fernet_key=iv_key):
            raise ContaboInstanceCreationError(f"Failed saving password for instance ID {instance_id}")

        logger.info(f"Instance created successfully with ID: {instance_id} and project ID: {user_project_id}")
        return {
            "user_project_id": user_project_id,
            "instance_id": instance_id
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating Contabo instance: {e}")
        raise ContaboInstanceCreationError(f"Failed to create Contabo instance: {e}") from e
    except KeyError as e:
        logger.error(f"Unexpected response format from Contabo API: {e}")
        raise ContaboInstanceCreationError(f"Unexpected response format from Contabo API: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error during Contabo instance creation: {e}")
        raise ContaboInstanceCreationError(f"Unexpected error during Contabo instance creation: {e}") from e


def setup_instance_async(data: Dict[str, Any], result_queue: queue.Queue) -> None:
    """
    Asynchronously set up a VPS instance.

    :param data: Dictionary containing instance setup parameters
    :param result_queue: Queue to put the result of the setup process
    """
    try:
        result = create_ec2_instance(data)  # TODO: For MVP using AWS free tier
        if result:
            instance_id = result.get('instance_id')
            user_project_id = result.get('user_project_id')
            if instance_id and user_project_id:
                logger.info(f"VPS created. Instance ID: {instance_id}, User Project ID: {user_project_id}")
                result_queue.put(result)
            else:
                raise InstanceSetupError("Instance created but ID or User Project ID is missing")
        else:
            raise InstanceSetupError("Failed to create VPS instance")

    except ContaboInstanceCreationError as e:
        logger.error(f"Error creating VPS instance: {e}")
        result_queue.put({"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error during VPS setup: {e}")
        result_queue.put({"error": f"Unexpected error during VPS setup: {str(e)}"})


def _setup_instance_async(data: Dict[str, Any], result_queue: queue.Queue) -> None:
    """
    Asynchronously set up a VPS instance.

    :param data: Dictionary containing instance setup parameters
    :param result_queue: Queue to put the result of the setup process
    """
    try:
        result = create_instance(data)
        if result:
            instance_id = result.get('instance_id')
            user_project_id = result.get('user_project_id')
            if instance_id and user_project_id:
                logger.info(f"VPS created. Instance ID: {instance_id}, User Project ID: {user_project_id}")
                result_queue.put(result)
            else:
                raise InstanceSetupError("Instance created but ID or User Project ID is missing")
        else:
            raise InstanceSetupError("Failed to create VPS instance")

    except ContaboInstanceCreationError as e:
        logger.error(f"Error creating VPS instance: {e}")
        result_queue.put({"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error during VPS setup: {e}")
        result_queue.put({"error": f"Unexpected error during VPS setup: {str(e)}"})


def setup_instance(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Set up a VPS instance.

    :param data: Dictionary containing instance setup parameters
    :return: Dictionary containing setup result or None if setup failed
    :raises SetupInstanceError: Specific class if there's an error during instance setup
    """
    try:
        result_queue = queue.Queue()

        # Start the setup process in a new thread
        thread = threading.Thread(
            target=setup_instance_async,
            args=(data, result_queue)
        )
        thread.start()

        # Wait for the thread to finish and get the result
        thread.join()
        result = result_queue.get()

        if "error" in result:
            raise SetupInstanceError(result["error"])

        return result
    except queue.Empty:
        logger.error("Setup process timed out")
        raise SetupInstanceError("Instance setup process timed out")
    except Exception as e:
        logger.error(f"Error setting up instance: {e}")
        raise SetupInstanceError(f"Failed to set up instance: {str(e)}") from e


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def check_instance_status(instance_id: int) -> Dict[str, Any]:
    """
    Check Contabo instance status.

    :param instance_id: ID of the instance to check
    :return: Dictionary containing instance status information
    :raises InstanceStatusCheckError: If there's an error checking instance status
    """
    ip_address = None
    url = f"{CONTABO_API_COMPUTE_INSTANCE}/{instance_id}"
    ACCESS_TOKEN = get_access_token()

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'x-request-id': f'status-check-{int(time.time())}',
        'x-trace-id': f'trace-{int(time.time())}'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        instance_data = response.json()['data'][0]
        status = instance_data['status']

        logger.info(f"Instance {instance_id} status: {status}.")

        if status.lower() == 'running':
            ip_address = instance_data['ipConfig']['v4']['ip']
            if not update_instance_ip(instance_id=instance_id, ip_address=ip_address):
                logger.warning(f"Failed to update IP address for instance {instance_id}")

        return {
            'status': status,
            'ip_address': ip_address if status.lower() == 'running' else None
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking instance status: {e}")
        raise InstanceStatusCheckError(f"Failed to check instance status: {str(e)}") from e
    except KeyError as e:
        logger.error(f"Unexpected response format from Contabo API: {e}")
        raise InstanceStatusCheckError(f"Unexpected response format from Contabo API: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error during instance status check: {e}")
        raise InstanceStatusCheckError(f"Unexpected error during instance status check: {str(e)}") from e


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def cancel_instance(instance_id: int) -> bool:
    """
    Cancels a Contabo VPS instance.

    :param instance_id: ID of the instance to cancel
    :return: True if cancellation was successful, False otherwise
    :raises InstanceCancellationError: If there's an error during instance cancellation
    """
    url = f"{CONTABO_API_COMPUTE_INSTANCE}/{instance_id}/cancel"
    ACCESS_TOKEN = get_access_token()

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'x-request-id': str(uuid.uuid4()),
        'x-trace-id': str(uuid.uuid4())[:6]
    }

    try:
        logger.info(f"Attempting to cancel instance with ID: {instance_id}")
        response = requests.post(url, headers=headers, timeout=30)
        response.raise_for_status()
        logger.info(f"Instance {instance_id} cancelled successfully")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error cancelling instance {instance_id}: {e}")
        raise InstanceCancellationError(f"Failed to cancel instance {instance_id}: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error while cancelling instance {instance_id}: {e}")
        raise InstanceCancellationError(f"Unexpected error while cancelling instance {instance_id}: {str(e)}") from e


if __name__ == "__main__":
    pass
