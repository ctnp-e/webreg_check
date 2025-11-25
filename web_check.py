import requests
from bs4 import BeautifulSoup
import json
import time

URL = "https://www.reg.uci.edu/perl/WebSoc"
data = {"Department Name": "COMPSCI"}

WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_HERE"
LAST_VALUE_FILE = "lastvalue.txt"

TIME_CHECK = 120 #seconds

def send_message(msg):
    requests.post(WEBHOOK_URL, json={"content": msg})

def get_current_value():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")

    '''# Example: the value is inside <span id="price">
    value = soup.find("span", {"id": "price"}).text.strip()
    return value
    '''
    
    text = soup.get_text(separator="\n", strip=True)

    print(text)

def get_last_value():
    try:
        with open(LAST_VALUE_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def save_last_value(value):
    with open(LAST_VALUE_FILE, "w") as f:
        f.write(value)

while False:
    current = get_current_value()
    old = get_last_value()

    if old != current:
        send_message(f"Value changed!\nOld: {old}\nNew: {current}")
        save_last_value(current)

    time.sleep(TIME_CHECK)

# get_current_value()



session = requests.Session()

response = session.post(URL, data=data)
soup = BeautifulSoup(response.text, "html.parser")

text = soup.get_text(separator="\n", strip=True)

print(text)