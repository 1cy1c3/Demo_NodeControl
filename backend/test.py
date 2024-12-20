import logging
import urllib.parse
import requests
import json
import time
import hmac
import hashlib
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
APP_SECRET = os.getenv('APP_SECRET')
BASE_URL = "http://localhost:5000"  # Adjust if your Flask app is running on a different port or host


def generate_signature(method, endpoint, timestamp, data=None):
    url = f"{BASE_URL}{endpoint}"
    if method == 'GET' and data:
        query_string = urllib.parse.urlencode(sorted(data.items()))
        url += f"?{query_string}"

    signature_data = f"{timestamp}{method}{url}"

    if method == 'POST' and data:
        signature_data += json.dumps(data, sort_keys=True)

    signature_data = signature_data.replace(" ", "")
    logging.info(f"SIGDATA: {signature_data}")
    print(signature_data)

    return hmac.new(
        APP_SECRET.encode('utf-8'),
        signature_data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def make_request(method, endpoint, data=None):
    timestamp = str(int(time.time()))
    signature = generate_signature(method, endpoint, timestamp, data)
    headers = {
        'X-Timestamp': timestamp,
        'X-Signature': signature,
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream'
    }
    url = f"{BASE_URL}{endpoint}"
    response = None

    if method == 'GET':
        response = requests.get(url, headers=headers, params=data)
    elif method == 'POST':
        response = requests.post(url, headers=headers, json=data)

    return response


def setup_process():
    data = {
        "ip_address": "52.29.207.158",
    }

    print("Sending request...")
    instance_response = make_request('GET', '/stream_logs', data)
    print(f"Response received. Status code: {instance_response.status_code}")
    print(f"Response headers: {instance_response.headers}")

    if instance_response.status_code != 200:
        print(f"Error response: {instance_response.text}")
        return

    print("Attempting to stream logs:")
    try:
        for line in instance_response.iter_lines(decode_unicode=True):
            if line:
                print(f"Received: {line}")
            else:
                print("Received empty line")
    except Exception as e:
        print(f"Error while streaming: {e}")

    print("Log streaming attempt completed")


# Add this to your main block
if __name__ == "__main__":
    setup_process()
    print("\nTesting non-streaming request:")
