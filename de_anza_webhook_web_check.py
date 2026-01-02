import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import datetime


# Default placeholders
WEBHOOK_URL = ""
BOT_TOKEN = ""
CHANNEL_ID = 0
USER = 0
TIME_CHECK = 1800 # 30 Minutes
CLASS_NAME = "BIOL 40A"
URL = "https://www.deanza.edu/schedule/listings.html?dept=BIOL&t=W2026"

# Load Credentials
try:
    with open("inp.txt", "r") as f:
        for line in f:
            if "webhook:" in line:
                WEBHOOK_URL = line.split("webhook:")[1].strip()
            elif "bot_token:" in line:
                BOT_TOKEN = line.split("bot_token:")[1].strip()
            elif "channel_id:" in line:
                CHANNEL_ID = int(line.split("channel_id:")[1].strip())
            elif "user:" in line:
                USER = int(line.split("user:")[1].strip())
except FileNotFoundError:
    print("Warning: webhook_val.txt not found.")

def send_message(msg):
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json={"content": msg})
    else:
        print("Log (No Webhook): " + msg)

# --- CORRECTED ALERT FUNCTIONS ---

def alert(line):
    msg = (f"**CLASS OPEN! REGISTER NOW!**\n"
           f"**Listing:** {line[:30]}\n"
           f"<@{USER}>\n"
           f"[Link to Schedule]({URL})")
    send_message(msg)



def sad_alert(line_text):
    send_message(f"{line_text[:30]}... (Status: No Change)")


def log_val(line):
    with open("current_vals.txt", "a") as f:
        f.write(f"{round(time.time())} : {line}\n")

# --- MAIN SCRAPER ---

def GO():

    
    options = Options()
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=400,300")
    options.add_argument("--window-position=0,0")  # top-left
        
    driver = webdriver.Chrome(options=options)
    
    driver.get(URL)
    time.sleep(5) 

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")


    rows = soup.find_all("tr")
            
    for row in rows:
        
        row_text = row.get_text(" | ", strip=True)
        
        if CLASS_NAME in row_text.upper():
            
            log_val(row_text)
            
            if "OPEN" in row_text.upper() or "WL" in row_text.upper():
                alert(row_text)
            else:
                sad_alert(row_text)

    driver.quit()

def main():
    with open('current_vals.txt', 'w') as f:
        f.write("--- Log Started ---\n")
    
    print("Bot started. Press Ctrl+C to stop.")
    
    while True:
        GO()
        time.sleep(TIME_CHECK)
        

if __name__ == "__main__":
    main()