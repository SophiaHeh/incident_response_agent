import requests
import os

class SlackNotifier:
    def __init__(self, webhook_url=None):
        """
        Initialize the Slack webhook integration.
        """
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
        
    def send_alert(self, title, message, context=None):
        """
        Send a real-time incident alert to the configured Slack channel.
        """
        if not self.webhook_url:
            print("Warning: SLACK_WEBHOOK_URL is not set. Skipping Slack notification.")
            return False
            
        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 {title}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{message}*"
                    }
                }
            ]
        }
        
        if context:
            payload["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```\n{context}\n```"
                }
            })
            
        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")
            return False
