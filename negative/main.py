import functions_framework
import json
import base64
from google.cloud import language_v1
from google.cloud import secretmanager
import requests

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

@functions_framework.http
def negative_function(request):
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

    # Send to Slack if negative (score < -0.25 for consistency with your task)
    if sentiment.score < -0.25:
        slack_token = access_secret('slacktoken', '1046723826220')
        channel = 'CH83QLHLY'  # Negative channel ID
        slack_message = f"Negative feedback from {feedback['user_id']}: {text}"
        send_slack_message(slack_token, channel, slack_message)
        return 'Negative message processed and sent to Slack', 200
    return 'Message processed (not negative)', 200