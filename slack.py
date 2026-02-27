import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

"""
{'name': 'Gold', 'price': 5178.399902, 'symbol': 'XAU', 'updatedAt': '2026-02-27T02:56:24Z', 'updatedAtReadable': 'a few seconds ago'}
"""

def get_gold_price():
    response = requests.get('https://api.gold-api.com/price/XAU')
    if response.status_code == 200:
        data = response.json()

        format = {
            "name": data['name'],
            "price": data['price'],
            "symbol": data['symbol'],
            "tanggal": data['updatedAt']
        }
        return f"Harga emas saat ini adalah {format['price']} USD per {format['symbol']} (update: {format['tanggal']})"
    else:
        print(f"Failed to fetch gold price: {response.status_code}")
        return None

def send_slack_notification(message):
    payload = {
        "text": message
    }
    response = requests.post(SLACK_WEBHOOK_URL, json=payload)

    if response.status_code != 200:
        print(f"Failed to send Slack notification: {response.status_code}")

if __name__ == "__main__":
    gold_price = get_gold_price()
    if gold_price:
        send_slack_notification(gold_price)
        print("Notification sent to Slack!")
    else:
        print("Failed to retrieve gold price.")