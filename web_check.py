import requests
from bs4 import BeautifulSoup
import time
import os
import sys
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options

load_dotenv()

WEBHOOK_URL   = os.getenv("WEBHOOK_URL")
BOT_TOKEN     = os.getenv("BOT_TOKEN")
CHANNEL_ID    = int(os.getenv("CHANNEL_ID"))
USER          = int(os.getenv("USER_ID"))
SECTION_CODE  = os.getenv("SECTION_CODE")
TIME_CHECK    = int(os.getenv("CHECK_INTERVAL", 1800))

# Optional — if all three are set, a mismatch check runs at startup
DEPT          = os.getenv("DEPT")
COURSE_NUM    = os.getenv("COURSE_NUM")
INSTRUCTOR    = os.getenv("INSTRUCTOR")


def _make_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")  # recommended on Windows
    return webdriver.Chrome(options=options)


def _parse_enrollment(soup):
    """Find Max/Enr for SECTION_CODE in the results table. Returns (max, enr) or None."""
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if "Max" not in headers or "Enr" not in headers:
            continue
        max_idx = headers.index("Max")
        enr_idx = headers.index("Enr")
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if cells and cells[0].get_text(strip=True) == SECTION_CODE:
                return cells[max_idx].get_text(strip=True), cells[enr_idx].get_text(strip=True)
    return None


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


def validate_config():
    """If DEPT/COURSE_NUM/INSTRUCTOR are set, verify SECTION_CODE appears in their results."""
    if not all([DEPT, COURSE_NUM, INSTRUCTOR]):
        print(f"Starting in section-code-only mode (section {SECTION_CODE}).")
        return

    print(f"Validating: checking that section {SECTION_CODE} matches {DEPT} / {COURSE_NUM} / {INSTRUCTOR}...")

    driver = _make_driver()
    driver.get("https://www.reg.uci.edu/perl/WebSoc")

    Select(driver.find_element(By.NAME, "Dept")).select_by_visible_text(DEPT)
    time.sleep(0.1)
    driver.find_element(By.NAME, "CourseNum").send_keys(COURSE_NUM)
    driver.find_element(By.NAME, "InstrName").send_keys(INSTRUCTOR)
    driver.find_element(By.XPATH, "//input[@type='submit' and @value='Display Web Results']").click()
    time.sleep(0.5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    result = _parse_enrollment(soup)
    if result is None:
        print(
            f"\n  MISMATCH: section {SECTION_CODE} was NOT found under "
            f"{DEPT} / {COURSE_NUM} / {INSTRUCTOR}.\n"
            f"  Double-check your .env values. Exiting."
        )
        sys.exit(1)

    print(f"  OK — section {SECTION_CODE} confirmed (Max={result[0]}, Enr={result[1]}).")


def GO():
    driver = _make_driver()
    driver.get("https://www.reg.uci.edu/perl/WebSoc")

    driver.find_element(By.NAME, "CourseCodes").send_keys(SECTION_CODE)
    driver.find_element(By.XPATH, "//input[@type='submit' and @value='Display Web Results']").click()
    time.sleep(0.5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    result = _parse_enrollment(soup)
    if result is None:
        print(f"Section {SECTION_CODE} not found in results — check the section code and quarter.")
        return

    record_and_alert(*result)


def main():
    validate_config()
    open('current_vals.txt', 'w').close()

    while True:
        GO()
        time.sleep(TIME_CHECK)


if __name__ == "__main__":
    main()
