import os
import json
import base64
from google.cloud import language_v1
from google.cloud import secretmanager
import requests
from flask import Flask, request

app = Flask(__name__)

def access_secret(secret_id: str, project_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    secret_name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": secret_name})
    secret_payload = response.payload.data.decode("UTF-8")
    return secret_payload

def send_slack_message(token, channel, message):
    url = 'https://slack.com/api/chat.postMessage'
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    data = {'channel': channel, 'text': message}
    response = requests.post(url, headers=headers, json=data)
    if not response.ok:
        print(f"Failed to send Slack message: {response.text}")
    return response.ok

@app.route('/', methods=['POST'])
def positive_function():
    # Parse the Pub/Sub push message
    if not request.is_json:
        return 'Invalid request: Expected JSON', 400

    envelope = request.get_json()
    if 'message' not in envelope:
        return 'Invalid Pub/Sub message: Missing message field', 400

    # Decode the message data
    message_data = envelope['message']['data']
    decoded_data = base64.b64decode(message_data).decode('utf-8')
    feedback = json.loads(decoded_data)
    text = feedback['message']

    # Analyze sentiment
    client = language_v1.LanguageServiceClient()
    document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
    sentiment = client.analyze_sentiment(request={'document': document}).document_sentiment

    # Send to Slack if positive
    if sentiment.score > 0.25:
        slack_token = access_secret('slacktoken', '1046723826220')
        channel = 'C08KN71G5S7'  # Positive channel ID
        slack_message = f"Positive feedback from {feedback['user_id']}: {text}"
        send_slack_message(slack_token, channel, slack_message)
        return 'Positive message processed and sent to Slack', 200
    return 'Message processed (not positive)', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)