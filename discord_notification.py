import requests


class DiscordNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_notification(self, message: str) -> bool:
        embed = {
            "title": "🛒 Stock Replenishment Required",
            "description": message
        }
        payload = {"embeds": [embed]}
        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Failed to send notification: {e}")
            return False
