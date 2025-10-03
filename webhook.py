from flask import Flask, request
from flask_cors import CORS
import requests
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ALLOWED_ORIGIN = os.environ.get('CORS_ORIGIN', 'https://firstblock.grafana.net')
SECRET_API_KEY = os.environ.get('SECRET_API_KEY')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ALLOWED_ORIGIN}})

@app.route('/<agent_type>/<action_name>', methods=['POST', 'OPTIONS'])
def handle_action(agent_type, action_name):
    """
    Entry point that validates security and then forwards the command
    to the dynamic destination (IP:Port) provided by Grafana.
    """
    if request.method == 'OPTIONS':
        return '', 204

    # 1. SECURITY CHECK: API Key
    auth_header = request.headers.get('X-API-Key')
    if not SECRET_API_KEY or auth_header != SECRET_API_KEY:
        logging.warning(f"Unauthorized access rejected (invalid or missing API key).")
        return "Unauthorized", 401

    # 2. DYNAMIC FORWARDING
    try:
        grafana_data = request.get_json()
        target_agent = grafana_data.get('agent')
        
        if not target_agent:
            logging.error("Target agent ('agent') key missing in the request payload.")
            return "Request body must contain 'agent' key with 'ip:port' value.", 400

        # Dynamically builds the forwarding URL.
        forward_url = f"http://{target_agent}/{action_name}"

        logging.info(f"Action '{action_name}' for agent '{agent_type}'. Forwarding to: {forward_url}")
        logging.info(f"Received payload: {grafana_data}")

        # 3. FORWARD THE COMMAND
        response = requests.post(forward_url, json=grafana_data, timeout=10)
        
        logging.info(f"Forward successful. Agent at {target_agent} responded with status: {response.status_code}")
        
        return (response.text, response.status_code, response.headers.items())

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to forward to agent at {target_agent}: {e}")
        return "Error forwarding request to internal agent", 502
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return "Internal Server Error", 500

if __name__ == '__main__':
    if not SECRET_API_KEY:
        logging.error("CRITICAL ERROR: SECRET_API_KEY environment variable is not set. Shutting down.")
    else:
        logging.info("Starting decentralized webhook service with dynamic forwarding...")
        app.run(host='0.0.0.0', port=30001)

