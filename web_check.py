import requests
from bs4 import BeautifulSoup
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time



WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_HERE"
LAST_VALUE_FILE = "lastvalue.txt"

TIME_CHECK = 120 #seconds


# Configure your driver (Chrome in this example)
driver = webdriver.Chrome()

# Load WebSOC page
driver.get("https://www.reg.uci.edu/perl/WebSoc")

# 2. Select department drop-down
dept_dropdown = Select(driver.find_element(By.NAME, "Dept")) 
dept_dropdown.select_by_visible_text("COMPSCI . . . . Computer Science")
time.sleep(1)


input_box = driver.find_element(By.NAME, "CourseNum")
input_box.send_keys("142a")


input_box = driver.find_element(By.NAME, "InstrName")
input_box.send_keys("demsky")

# 3. Submit search
driver.find_element(By.XPATH, "//input[@type='submit' and @value='Display Text Results']").click()
time.sleep(2)  # wait for results to load

html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

text = soup.get_text(separator="\n", strip=True)
for line in text.splitlines():
    if "34130" in line :
        print(line)

# print(text)

def send_message(msg):
    requests.post(WEBHOOK_URL, json={"content": msg})

def get_current_value():
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
