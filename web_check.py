import requests
from bs4 import BeautifulSoup
import time
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

load_dotenv()

WEBHOOK_URL   = os.getenv("WEBHOOK_URL")
BOT_TOKEN     = os.getenv("BOT_TOKEN")
CHANNEL_ID    = int(os.getenv("CHANNEL_ID"))
USER          = int(os.getenv("USER_ID"))
SECTION_CODE  = os.getenv("SECTION_CODE")
TIME_CHECK    = int(os.getenv("CHECK_INTERVAL", 1800))


def send_message(msg):
    requests.post(WEBHOOK_URL, json={"content": msg})

def alert(max_enroll, curr_enroll):
    send_message(f"Value changed! REGISTER NOW!\nMAX: {max_enroll}\tCURR: {curr_enroll} <@{USER}>")

def sad_alert(max_enroll, curr_enroll):
    send_message(f"No change detected... :( \t\t MAX: {max_enroll}\tCURR: {curr_enroll}")

def record_and_alert(max_enroll, curr_enroll):
    print(f"MAX: {max_enroll}  ENR: {curr_enroll}")
    if curr_enroll != max_enroll:
        alert(max_enroll, curr_enroll)
    else:
        sad_alert(max_enroll, curr_enroll)
    with open("current_vals.txt", "a") as f:
        f.write(f"{round(time.time())} : {max_enroll} {curr_enroll}\n")


def GO():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")  # recommended on Windows

    driver = webdriver.Chrome(options=options)
    driver.get("https://www.reg.uci.edu/perl/WebSoc")

    # Search by section code only — no dept/instructor needed
    driver.find_element(By.NAME, "CourseCodes").send_keys(SECTION_CODE)
    driver.find_element(By.XPATH, "//input[@type='submit' and @value='Display Web Results']").click()
    time.sleep(0.5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    # Find the enrollment table by locating the header row with "Max" and "Enr"
    for table in soup.find_all("table"):
        header_cells = table.find_all("th")
        if not header_cells:
            continue
        headers = [th.get_text(strip=True) for th in header_cells]
        if "Max" not in headers or "Enr" not in headers:
            continue

        max_idx = headers.index("Max")
        enr_idx = headers.index("Enr")

        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if not cells:
                continue
            if cells[0].get_text(strip=True) == SECTION_CODE:
                max_enroll  = cells[max_idx].get_text(strip=True)
                curr_enroll = cells[enr_idx].get_text(strip=True)
                record_and_alert(max_enroll, curr_enroll)
                return

    print(f"Section {SECTION_CODE} not found in results — check that the section code is correct and the quarter is active.")


def main():
    open('current_vals.txt', 'w').close()

    while True:
        GO()
        time.sleep(TIME_CHECK)


if __name__ == "__main__":
    main()
