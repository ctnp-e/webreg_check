import requests
from bs4 import BeautifulSoup
import time
import os
import sys
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
BOT_TOKEN   = os.getenv("BOT_TOKEN")
CHANNEL_ID  = int(os.getenv("CHANNEL_ID"))
USER        = int(os.getenv("USER_ID"))
CLASS_NAME  = os.getenv("CLASS_NAME")
URL         = os.getenv("CLASS_URL")
TIME_CHECK  = int(os.getenv("CHECK_INTERVAL", 1800))


def send_message(msg):
    requests.post(WEBHOOK_URL, json={"content": msg})

def alert(row_text):
    send_message(
        f"**CLASS OPEN! REGISTER NOW!**\n"
        f"**Listing:** {row_text[:80]}\n"
        f"<@{USER}>\n"
        f"[Link to Schedule]({URL})"
    )

def sad_alert(row_text):
    send_message(f"{row_text[:80]}... (no change)")

def log_val(line):
    with open("current_vals.txt", "a") as f:
        f.write(f"{round(time.time())} : {line}\n")


def GO():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)
    driver.get(URL)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    found = False
    for row in soup.find_all("tr"):
        row_text = row.get_text(" | ", strip=True)
        if CLASS_NAME.upper() in row_text.upper():
            found = True
            log_val(row_text)
            if "OPEN" in row_text.upper() or "WL" in row_text.upper():
                alert(row_text)
            else:
                sad_alert(row_text)

    if not found:
        print(f"  {CLASS_NAME} not found on page — check CLASS_NAME and CLASS_URL in .env.")


def main():
    print(f"Monitoring {CLASS_NAME} on De Anza schedule...")
    with open("current_vals.txt", "w") as f:
        f.write("--- Log Started ---\n")

    while True:
        GO()
        time.sleep(TIME_CHECK)


if __name__ == "__main__":
    main()
