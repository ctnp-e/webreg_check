import requests
from bs4 import BeautifulSoup
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
import time


with open("webhook_val.txt", "r") as f:
    for line in f:
        if "webhook:" in line:
            WEBHOOK_URL = line.split("webhook:")[1].strip()
        elif "bot_token:" in line:
            BOT_TOKEN = line.split("bot_token:")[1].strip()
        elif "channel_id:" in line:
            CHANNEL_ID = int(line.split("channel_id:")[1].strip())
        elif "user:" in line:
            USER = int(line.split("user:")[1].strip())
    #print(data)

# WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_HERE"
LAST_VALUE_FILE = "lastvalue.txt"
TIME_CHECK = 1800 #seconds



# print(text)

def send_message(msg):
    requests.post(WEBHOOK_URL, json={"content": msg})

def alert(max, curr):
    send_message(f"Value changed! REGISTER NOW!\nMAX: {max}\tCURR: {curr} <@{USER}>")

def sad_alert(max, curr) :
    send_message(f"No change detected... :( \t\t MAX: {max}\tCURR: {curr}")

def add_to_curr_vals(particular_inp) :
    result = particular_inp.strip().split(" ")
    result = [x for x in result if x.strip()]

    # ohyea = 0
    # for line in result:
    #     print(str(ohyea) + " : " + line)
    #     ohyea += 1
    
    '''
    total_len = len(result)
    max = result[total_len-7]
    curr = result[total_len-6]
    # curr = 1 #testing
    if (curr != max) :
        alert(max, curr)
    else :
        sad_alert(max, curr)

    print_to_curr_vals( str(max) + " " + str(curr))
    '''
    
    print_to_curr_vals( particular_inp)


def print_to_curr_vals(line) :
    with open("current_vals.txt", "a") as f:
        f.write(str(round(time.time())) + " : " + line + "\n")
    


def GO() :

    options = Options()
    options.add_argument("--headless")              # Chrome runs with NO window
    options.add_argument("--disable-gpu")           # recommended on Windows
    
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.deanza.edu/schedule/listings.html?dept=BIOL&t=W2026") # loads DE ANZA page


    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    particular_inp = ""
    # finds exact course
    text = soup.get_text(separator="\n", strip=True)
    for line in text.splitlines():
        if "BIOL 40A" in line :
            add_to_curr_vals(line)
    
    
    driver.quit()


def main():

    open('current_vals.txt', 'w').close()
    
    while True:
        GO()
        time.sleep(TIME_CHECK)

GO()