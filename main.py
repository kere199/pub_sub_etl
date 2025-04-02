import os
from google.cloud import pubsub_v1
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuration
PROJECT_ID = "vital-cathode-454012-k0"
TOPIC_ID = "keres_topic"

# Initialize Pub/Sub publisher
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

@app.route('/', methods=['POST'])
def process_feedback():
    """Process feedback and publish to Pub/Sub."""
    try:
        if request.method != 'POST':
            return jsonify({'error': 'Method not allowed'}), 405

        data = request.get_json()
        
        if not data or 'user_id' not in data or 'message' not in data:
            return jsonify({
                'error': 'Invalid request: user_id and message are required'
            }), 400

        user_id = data['user_id']
        message = data['message']

        message_data = json.dumps({
            'user_id': user_id,
            'message': message
        }).encode('utf-8')

        future = publisher.publish(topic_path, message_data)
        message_id = future.result()

        return jsonify({
            'status': 'success',
            'message_id': message_id,
            'user_id': user_id
        }), 200

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)