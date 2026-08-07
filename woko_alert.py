import os
import json
import hashlib
import requests
from bs4 import BeautifulSoup

WOKO_URL = "https://www.woko.ch/en/our-service/available-units"

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

STATE_FILE = "seen.json"


def get_page():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/130 Safari/537.36"
        )
    }

    response = requests.get(
        WOKO_URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()
    return response.text


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "disable_web_page_preview": False,
    }

    response = requests.post(
        url,
        data=data,
        timeout=30
    )

    response.raise_for_status()


def load_seen():
    if not os.path.exists(STATE_FILE):
        return set()

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return set(json.load(f))


def save_seen(seen):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f)


def make_id(text):
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def main():

    html = get_page()

    soup = BeautifulSoup(html, "html.parser")

    seen = load_seen()
    current = set()

    # WOKO listing cards
    listings = soup.select("article")

    print(f"Found {len(listings)} listings")

    for listing in listings:

        text = listing.get_text(
            " ",
            strip=True
        )

        if not text:
            continue

        listing_id = make_id(text)

        current.add(listing_id)

        if listing_id in seen:
            continue

        # First run: don't send all existing listings
        if not seen:
            continue

        message = (
            "🚨 NEW WOKO UNIT\n\n"
            f"{text[:3000]}\n\n"
            f"🔗 {WOKO_URL}"
        )

        send_telegram(message)

    save_seen(current)


if __name__ == "__main__":
    main()
