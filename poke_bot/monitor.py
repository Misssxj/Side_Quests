import json
import os

import requests
from bs4 import BeautifulSoup


PRODUCT_NAME = "Pokémon Trading Card Game: 30th Celebration Elite Trainer Box"

PRODUCT_URL = "https://www.target.com/p/pok-233-mon-trading-card-game-30th-celebration-elite-trainer-box/-/A-1010892076"

OUT_OF_STOCK_TEXT = "out of stock"

PRODUCT_MARKER = "30th celebration elite trainer box"


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "state.json")


def check_stock():

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        PRODUCT_URL,
        headers=headers,
        timeout=20
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    page_text = soup.get_text(
        " ",
        strip=True
    ).lower()

    if PRODUCT_MARKER.lower() not in page_text:
        raise RuntimeError(
            "Could not verify the Target product page. "
            "Target may have blocked the request."
        )

    return OUT_OF_STOCK_TEXT.lower() not in page_text

def send_discord_alert():

    webhook = os.environ["DISCORD_WEBHOOK"]

    message = {
        "content": (
            "🚨 **POKÉMON RESTOCK DETECTED**\n\n"
            f"**{PRODUCT_NAME}**\n"
            "Appears to be IN STOCK!\n\n"
            f"{PRODUCT_URL}"
        )
    }

    response = requests.post(
        webhook,
        json=message,
        timeout=20
    )

    response.raise_for_status()


try:

    with open(STATE_FILE, "r") as file:
        state = json.load(file)

except FileNotFoundError:

    state = {
        "in_stock": False
    }


previous_stock = state.get(
    "in_stock",
    False
)


current_stock = check_stock()

print("Product:", PRODUCT_NAME)
print("Previous stock:", previous_stock)
print("Current stock:", current_stock)


if current_stock and not previous_stock:

    print("RESTOCK DETECTED!")

    send_discord_alert()


elif not current_stock and previous_stock:

    print("Product went out of stock.")


else:

    print("No stock change.")


state["in_stock"] = current_stock

with open(STATE_FILE, "w") as file:

    json.dump(
        state,
        file,
        indent=2
    )
