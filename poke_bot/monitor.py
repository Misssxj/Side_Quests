import json
import os
import re

import requests
from playwright.sync_api import sync_playwright


PRODUCT_NAME = "Pokémon Trading Card Game: 30th Celebration Elite Trainer Box"

PRODUCT_URL = (
    "https://www.target.com/p/"
    "pok-233-mon-trading-card-game-30th-celebration-elite-trainer-box/"
    "-/A-1010892076"
)

PRODUCT_MARKER = "30th celebration elite trainer box"


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "state.json")


def check_stock():

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        page.goto(
            PRODUCT_URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        # Give Target time to load the product information
        page.wait_for_timeout(5000)

        page_text = page.locator("body").inner_text().lower()

        # Verify that Target loaded the correct product
        if PRODUCT_MARKER not in page_text:
            browser.close()

            raise RuntimeError(
                "Could not verify Target product page. "
                "No Discord alert was sent."
            )

        # First check for an explicit Out of Stock message
        out_of_stock = page.get_by_text(
            "Out of Stock",
            exact=True
        )

        if out_of_stock.count() > 0:

            for i in range(out_of_stock.count()):

                if out_of_stock.nth(i).is_visible():

                    print("Target displays: Out of Stock")

                    browser.close()

                    return False


        # If it does not say Out of Stock,
        # inspect the first visible Add to cart button
        buttons = page.get_by_role(
            "button",
            name=re.compile(
                r"add to cart",
                re.IGNORECASE
            )
        )

        for i in range(buttons.count()):

            button = buttons.nth(i)

            if button.is_visible():

                enabled = button.is_enabled()

                print(
                    "Main Add to cart button enabled:",
                    enabled
                )

                browser.close()

                return enabled


        browser.close()

        # Never assume stock if Target gives us an unclear page
        raise RuntimeError(
            "Could not safely determine Target stock status. "
            "No Discord alert was sent."
        )


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
