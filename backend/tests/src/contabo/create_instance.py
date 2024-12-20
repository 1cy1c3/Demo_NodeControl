import os
import threading
import json
import requests
import uuid
import logging
import time
import queue

from flask import Flask
from flask_cors import CORS
from requests.exceptions import RequestException
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv
from src.database.database import update_instance_ip, generate_password_and_key, save_encrypted_password, create_user_project


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


def get_access_token() -> str or None:
    headers = {
        'client_id': CONTABO_CLIENT_ID,
        'client_secret': CONTABO_CLIENT_SECRET,
        'username': CONTABO_API_USER,
        'password': CONTABO_API_SECRET,
        'grant_type': 'password'
    }

    try:
        response = requests.post(CONTABO_API_AUTH, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses

        token_data = response.json()
        print(token_data)
        return token_data['access_token']
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def create_instance(data: json) -> json or None:
    """
    Creates a new VPS instance with retry mechanism and improved error handling.
    """
    # Extract Values
    image_id = data.get('imageId')
    product_id = data.get('productId')
    region = data.get('region', 'EU')
    period = data.get('period', 1)
    display_name = data.get('displayName')
    default_user = data.get('defaultUser', 'root')
    project_id = data.get('project_id')
    user_id = data.get('user_id')

    password, iv_key = generate_password_and_key()
    ACCESS_TOKEN = get_access_token()

    if not ACCESS_TOKEN:
        logging.error("Error Fetching Access Token")
        return create_instance(data)

    if not password:
        logging.error("Error Creating Password")
        return create_instance(data)

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

    try:
        logger.info("Attempting to create VPS instance...")
        response = requests.post(CONTABO_API_COMPUTE_INSTANCE, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        response_data = response.json()

        instance_id = response_data['data'][0]['instanceId']
        user_project_id = create_user_project(user_id=user_id, project_id=project_id, instance_id=instance_id)

        if user_project_id:
            logger.info(f"Instance created successfully with ID: {instance_id} and project ID: {user_project_id}")

            if save_encrypted_password(user_project_id=user_project_id, password=password, fernet_key=iv_key):
                logger.info(f"Instance created successfully with ID: {instance_id} and project ID: {user_project_id}")
            else:
                logger.error(f"Failed creating save password for instance ID {instance_id}")
            return {
                "user_project_id": user_project_id,
                "instance_id": instance_id
            }

        logger.error(f"Failed creating user project for instance ID {instance_id}")
        return {
                "instance_id": instance_id
            }

    except RequestException as e:
        logger.error(f"Error creating instance: {e}")
        raise  # This will trigger a retry

    except KeyError as e:
        logger.error(f"Unexpected response format: {e}")
        return None

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None


def setup_instance_async(data: json, result_queue: queue.Queue):
    try:
        result = create_instance(data)
        if result:
            instance_id, password = result
            logger.info(f"VPS created. Instance ID: {instance_id}")
            result_queue.put(int(instance_id))
        else:
            logger.error("Failed to create VPS instance")
            result_queue.put(None)

    except Exception as e:
        logger.error(f"VPS creation failed after retries: {e}")
        result_queue.put(None)


def setup_instance(data: json) -> int or None:
    # Create a queue to get the result from the thread
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

        return result
    except Exception as e:
        logging.error(f"Error checking instance status: {e}")
        return None


def check_instance_status(instance_id: int) -> str:
    """
    Check Contabo instance status periodically for up to 48 hours.
    :param instance_id: ID of the instance to check
    """
    url = CONTABO_API_COMPUTE_INSTANCE + f'/{instance_id}'
    ACCESS_TOKEN = get_access_token()

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'x-request-id': 'status-check-{}'.format(int(time.time())),
        'x-trace-id': 'trace-{}'.format(int(time.time()))
    }

    status = 'unknown'

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        instance_data = response.json()['data'][0]
        status = instance_data['status']

        logging.info(f"Instance {instance_id} status: {status}.")

        if status.lower() == 'running':
            update_instance_ip(instance_id=instance_id, ip_address=instance_data['ipConfig']['v4']['ip'])

        return status

    except requests.exceptions.RequestException as e:
        logging.error(f"Error checking instance status: {e}")

    logging.warning(f"Instance {instance_id} is still provisioning, cannot fetch status")
    return status


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def cancel_instance(instance_id: int) -> bool:
    """
    Cancels a Contabo VPS instance.
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
    except RequestException as e:
        logger.error(f"Error cancelling instance {instance_id}: {e}")
        raise  # This will trigger a retry
    except Exception as e:
        logger.error(f"Unexpected error while cancelling instance {instance_id}: {e}")
        return False


if __name__ == "__main__":
    pass
