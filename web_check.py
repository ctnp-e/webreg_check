import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options


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

TIME_CHECK = 1800  # seconds between checks


def send_message(msg):
    requests.post(WEBHOOK_URL, json={"content": msg})

def alert(max_enroll, curr_enroll):
    send_message(f"Value changed! REGISTER NOW!\nMAX: {max_enroll}\tCURR: {curr_enroll} <@{USER}>")

def sad_alert(max_enroll, curr_enroll):
    send_message(f"No change detected... :( \t\t MAX: {max_enroll}\tCURR: {curr_enroll}")

def add_to_curr_vals(line):
    result = [x for x in line.strip().split(" ") if x.strip()]

    total_len = len(result)
    max_enroll = result[total_len - 7]
    curr_enroll = result[total_len - 6]

    if curr_enroll != max_enroll:
        alert(max_enroll, curr_enroll)
    else:
        sad_alert(max_enroll, curr_enroll)

    print_to_curr_vals(f"{max_enroll} {curr_enroll}")


def print_to_curr_vals(line):
    with open("current_vals.txt", "a") as f:
        f.write(f"{round(time.time())} : {line}\n")


def GO():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")  # recommended on Windows

    driver = webdriver.Chrome(options=options)
    driver.get("https://www.reg.uci.edu/perl/WebSoc")

    dept_dropdown = Select(driver.find_element(By.NAME, "Dept"))
    dept_dropdown.select_by_visible_text("COMPSCI . . . . Computer Science")
    time.sleep(0.1)

    driver.find_element(By.NAME, "CourseNum").send_keys("142a")
    driver.find_element(By.NAME, "InstrName").send_keys("demsky")

    driver.find_element(By.XPATH, "//input[@type='submit' and @value='Display Text Results']").click()
    time.sleep(0.5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    for line in soup.get_text(separator="\n", strip=True).splitlines():
        if "34130" in line:
            add_to_curr_vals(line)


def main():
    open('current_vals.txt', 'w').close()

    while True:
        GO()
        time.sleep(TIME_CHECK)


if __name__ == "__main__":
    main()