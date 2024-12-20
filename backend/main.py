import logging
import os
import hmac
import hashlib
import time
import json
import traceback

from functools import wraps
from flask_cors import CORS
from typing import List, Dict
from http.client import HTTPException
from werkzeug.exceptions import HTTPException
from flask import request, jsonify, Flask, Response

from src.aws.aws_instance import get_instance_status
from src.vps.connect_vps import setup_vps, vps_logs_stream
from src.crypto.create_wallet import generate_wallet_keys
from src.contabo.create_instance import setup_instance, check_instance_status, cancel_instance
from src.database.database import (create_user_project, register_user, login_user, send_verification_email,
                                   verify_email_process, fetch_user_projects)

# from src.contabo.batch_process import initialize_scheduler

from dotenv import load_dotenv

# Get the APP_SECRET from the .env file
load_dotenv()
APP_SECRET = os.getenv('APP_SECRET')
CONTABO_CLIENT_ID = os.getenv('CONTABO_CLIENT_ID')
CONTABO_CLIENT_SECRET = os.getenv('CONTABO_CLIENT_SECRET')
CONTABO_API_USER = os.getenv('CONTABO_API_USER')
CONTABO_API_SECRET = os.getenv('CONTABO_API_SECRET')

if not APP_SECRET:
    raise ValueError("APP_SECRET is not set in the .env file")

# Initialize flask
app = Flask(__name__)
CORS(app, resources={r"/*": {
    "origins": "*",  # Be more specific in production
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization", "X-Signature", "X-Timestamp"],
    "expose_headers": ["Content-Type", "Authorization", "X-Signature", "X-Timestamp"],
    "supports_credentials": True,
    "vary_header": True
}})


# Initialize batch process to check on running instances
# initialize_scheduler()


@app.errorhandler(Exception)
def handle_error(error):
    error_details = {
        'type': str(type(error).__name__),
        'message': str(error),
        'traceback': traceback.format_exc()
    }

    if isinstance(error, HTTPException):
        error_details['code'] = error.code
        response = jsonify(error_details)
        response.status_code = error.code
    else:
        error_details['code'] = 500
        response = jsonify(error_details)
        response.status_code = 500

    logging.error(
        f"Error occurred: {error_details['type']}\nMessage: {error_details['message']}\nTraceback:\n{error_details['traceback']}")

    return response


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Signature,X-Timestamp')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response


def verify_signature(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'OPTIONS':
            return '', 200

        timestamp = request.headers.get('X-Timestamp')
        provided_signature = request.headers.get('X-Signature')

        if not timestamp or not provided_signature:
            return jsonify({'error': 'Missing headers'}), 401

        if abs(int(time.time()) - int(timestamp)) > 1000:
            return jsonify({'error': 'Request expired'}), 401

        url = request.base_url
        if request.query_string:
            url += '?' + request.query_string.decode()

        signature_data = f"{timestamp}{request.method}{url}"

        # Only add JSON body for POST requests
        if request.method == 'POST' and request.is_json:
            json_data = request.get_json(silent=True)
            if json_data:
                signature_data += json.dumps(json_data, sort_keys=True)

        signature_data = signature_data.replace(" ", "")
        logging.info(f"Final SIGNATURE DATA: {signature_data}")

        expected_signature = hmac.new(
            APP_SECRET.encode('utf-8'),
            signature_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        logging.info(f"Provided Signature: {provided_signature}")
        logging.info(f"Expected Signature: {expected_signature}")

        if not hmac.compare_digest(provided_signature, expected_signature):
            return jsonify({'error': 'Invalid signature'}), 401

        return f(*args, **kwargs)

    return decorated


@app.route('/instance_setup', methods=['POST', 'GET'])
@verify_signature
def instance_setup() -> json:
    try:
        data = request.json
        response = setup_instance(data)

        if "instance_id" in response and "user_project_id" in response and "public_ip" in response:
            return jsonify({
                'message': f"Instance created",
                'user_project_id': response['user_project_id'],
                'instance_id': response['instance_id']
            }), 202  # 202 Accepted

        return jsonify({
            'message': f"Unexpected problem while instance creation. Please contact support.",
            f'Response': response
        }), 500

    except Exception as e:
        # Log the exception or handle it appropriately
        return jsonify({'error': str(e)}), 500


@app.route('/user_projects', methods=['GET'])
@verify_signature
def get_user_projects():
    if request.method == 'OPTIONS':
        return '', 200

    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        user_project_data = fetch_user_projects(int(user_id))
        return jsonify({"message": "User project data successfully fetched", "data": user_project_data}), 200
    except Exception as e:
        logging.error(f"Error in get_user_projects: {str(e)}")
        raise


@app.route('/instance_status', methods=['GET'])
@verify_signature
def instance_status() -> json:
    def parse_instance_ids(input_data: str) -> List[str]:
        # Check if input_data is already a list
        instance_ids = input_data.split("instance_ids%5B%5D=")
        for i in range(len(instance_ids)):
            if "&" in instance_ids[i]:
                instance_ids[i] = instance_ids[i].replace("&", "")
        return instance_ids

    try:
        instance_ids_raw = request.args.get('params')
        instance_ids = parse_instance_ids(instance_ids_raw)
        if not instance_ids:
            return jsonify({'error': 'No instance IDs provided'}), 400

        statuses: List[Dict] = []
        errors: List[Dict] = []

        for instance_id in instance_ids:
            try:
                status = get_instance_status(instance_id)
                statuses.append({
                    'instanceId': instance_id,
                    'status': status,
                })
            except Exception as e:
                logging.error(f"Error fetching status for instance {instance_id}: {str(e)}")
                errors.append({
                    'instanceId': instance_id,
                    'error': str(e)
                })

        response = {
            'statuses': statuses,
            'errors': errors
        }

        return jsonify(response), 200

    except Exception as e:
        logging.error(f"Unexpected error in instance_status: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.route('/_instance_status', methods=['GET'])
@verify_signature
def _instance_status() -> json:
    try:
        data = request.json
        instance_id = data.get('instanceId')
        status = check_instance_status(instance_id)
        return jsonify({
            f'status': f'{status["status"]}',
            'ip_address': status["ip_address"] if status["status"].lower() == 'running' else None
        }), 202  # 202 Accepted
    except Exception as e:
        # Log the exception or handle it appropriately
        return jsonify({'error': str(e)}), 500


@app.route('/vps_setup', methods=['POST', 'GET'])
@verify_signature
def vps_setup() -> json:
    try:
        data = request.json
        setup_vps(data['user_project_id'])
        return jsonify({
            'status': f'Instance created, setup started',
        }), 202  # 202 Accepted
    except Exception as e:
        # Log the exception or handle it appropriately
        return jsonify({'error': str(e)}), 500


@app.route('/register', methods=['POST'])
@verify_signature
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    user_id, verification_token, error = register_user(username, email, password)

    if error:
        return jsonify({"error": error}), 400

    try:
        send_verification_email(email, verification_token)
    except Exception as e:
        return jsonify({"error": f"Failed to send verification email: {str(e)}"}), 500

    return jsonify({"message": "User registered successfully. Please check your email to verify your account.",
                    "userId": user_id}), 201


@app.route('/verify_email', methods=['GET'])
def verify_email():
    token = request.args.get('token')
    email = request.args.get('email')
    if not token or not email:
        return jsonify({"error": "Both token and email are required"}), 400

    if verify_email_process(token=token, email=email):
        return jsonify({"status": "Successfully verified"}), 202
    else:
        return jsonify({"error": "Email couldn't be verified"}), 500


@app.route('/login', methods=['POST'])
@verify_signature
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    ip_address = request.remote_addr

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user_id, user_name, error_message = login_user(email, password, ip_address)

    if user_id and user_name:
        return jsonify({"message": "Login successful", "user_id": user_id, "user_name": user_name}), 201
    else:
        return jsonify({"error": error_message}), 401


@app.route('/create_project', methods=['POST'])
@verify_signature
def create_project():
    try:
        data = request.json
        project_id = create_user_project(data['user_id'], data['project_id'], data['version'])
        if project_id is None:
            return jsonify({'error': 'Failed to create project'}), 400
        return jsonify({'project_id': project_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/cancel_instance/<instance_id>', methods=['POST'])
@verify_signature
def cancel_instance():
    try:
        data = request.json
        result = cancel_instance(data['instanceId'])
        if result:
            return jsonify({'message': f'Instance {data["instanceId"]} cancelled successfully'}), 200
        else:
            return jsonify({'error': f'Failed to cancel instance {data["instanceId"]}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/generate_wallet', methods=['POST'])
@verify_signature
def generate_wallet():
    try:
        data = request.json
        wallet_type = data.get('wallet_type')
        user_project_id = data.get('user_project_id')

        if not wallet_type:
            return jsonify({'error': 'Wallet type is required'}), 400

        wallet_keys = generate_wallet_keys(wallet_type, user_project_id=user_project_id)

        # For security reasons, we might not want to send the private key directly in the response
        # Instead, we could save it securely and return a reference, or implement a secure way to transmit it
        return jsonify({
            'message': f'{wallet_type.capitalize()} wallet generated successfully',
            'public_key': wallet_keys['public_key']
        }), 201
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500


@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    return '', 200


@app.route('/stream_logs', methods=['GET'])
@verify_signature
def stream_logs():
    ip_address = request.args.get('ip_address')
    if not ip_address:
        return jsonify({"error": "Invalid Request, missing IP"}), 400

    def generate():
        try:
            for line in vps_logs_stream(instanceIp=ip_address, pem=True):
                print(f"Sending line: {line}")
                yield f"data: {line}\n\n"
        except GeneratorExit:
            logging.info(f"Stream Ended\n\n")
            yield f"data: Stream Ended\n\n"

    return Response(generate(), content_type='text/event-stream')


@app.route('/stream', methods=['GET'])
def stream_numbers():
    def generate_numbers():
        for i in range(1, 101):
            yield f"data: {i}\n\n"
            time.sleep(0.1)

    return Response(generate_numbers(), content_type='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
