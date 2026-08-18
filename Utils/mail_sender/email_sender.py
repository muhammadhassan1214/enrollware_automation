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


def send_email(subject: str, html_content: str, send_to_email: str, send_to_name: str) -> bool:
    payload = {
          "sender": {
            "name": "Code Blue CPR Services",
            "email": os.getenv("SENDER_EMAIL")
          },
          "to": [
            {
              "email": send_to_email,
              "name": send_to_name
            }
          ],
          "subject": subject,
          "htmlContent": html_content
        }


    try:
        response = requests.post(URL, json=payload, headers=headers)
        if response.status_code == 201:
            return True
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Connection Error: {e}")
        return False
