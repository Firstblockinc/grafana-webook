from flask import Flask, request
from flask_cors import CORS
import requests
import os


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
        
        print(f"✅ Action reçue '{action_name}'. Transfert vers : {forward_url}")
        
        try:
            grafana_data = request.get_json()
            
            response = requests.post(forward_url, json=grafana_data, timeout=5)
            
            return (response.text, response.status_code, response.headers.items())

        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors du transfert vers l'agent : {e}")
            return "Erreur lors du transfert de la requête à l'agent interne", 502
            
# --- Démarrage de l'application ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=30001)
