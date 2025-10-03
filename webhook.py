from flask import Flask, request
from flask_cors import CORS
import requests
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


AGENT_BASE_URL = os.environ.get('AGENT_URL', 'http://172.20.0.84:22001')
ALLOWED_ORIGIN = os.environ.get('CORS_ORIGIN', 'https://firstblock.grafana.net')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ALLOWED_ORIGIN}})


@app.route('/action/<action_name>', methods=['POST', 'OPTIONS'])
def handle_dynamic_action(action_name):
    if request.method == 'OPTIONS':
        return '', 204

    if request.method == 'POST':
        forward_url = f"{AGENT_BASE_URL}/{action_name}"
        
        logging.info(f"Action reçue '{action_name}'. Transfert vers : {forward_url}")
        
        try:

            grafana_data = request.get_json()
            logging.info(f"Payload reçu de Grafana : {grafana_data}")
            

            response = requests.post(forward_url, json=grafana_data, timeout=5)
            
            logging.info(f"Transfert réussi. L'agent a répondu avec le statut : {response.status_code}")
            
            return (response.text, response.status_code, response.headers.items())

        except requests.exceptions.RequestException as e:
            logging.error(f"Échec du transfert vers l'agent : {e}")
            return "Error forwarding request to internal agent", 502
            

if __name__ == '__main__':
    logging.info("Démarrage du service webhook proxy...")
    app.run(host='0.0.0.0', port=30001)

