import os
import requests
from dotenv import load_dotenv


load_dotenv()
URL = "https://api.brevo.com/v3/smtp/email"
headers = {
    "accept": "application/json",
    "api-key": os.getenv("BREVO_API_KEY"),
    "content-type": "application/json"
}


def send_email(text_content):
    send_to_email = os.getenv("NATHAN_EMAIL")
    payload = {
          "sender": {
            "name": "Code Blue CPR Services",
            "email": os.getenv("SENDER_EMAIL")
          },
          "to": [
            {
              "email": send_to_email,
              "name": "Nathaniel Shell"
            }
          ],
          "subject": "🛒 Stock Replenishment Required",
          "textContent": text_content
        }


    try:
        response = requests.post(URL, json=payload, headers=headers)
        if response.status_code == 201:
            print(f"🛒 Stock Replenishment email sent successfully to {send_to_email}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Connection Error: {e}")
