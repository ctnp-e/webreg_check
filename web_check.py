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

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
BOT_TOKEN   = os.getenv("BOT_TOKEN")
CHANNEL_ID  = int(os.getenv("CHANNEL_ID"))
USER        = int(os.getenv("USER_ID"))
TIME_CHECK  = int(os.getenv("CHECK_INTERVAL", 1800))


# ---------- load classes.txt ----------

def load_classes():
    if not os.path.exists("classes.txt"):
        print(
            "ERROR: classes.txt not found.\n"
            "Create a classes.txt file in the same folder as this script.\n"
            "See classes.txt.example for instructions."
        )
        sys.exit(1)

    classes = []
    with open("classes.txt") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            parts = [p.strip() for p in line.split(",")]

            if len(parts) == 1:
                classes.append({"code": parts[0], "dept": None, "course_num": None, "instructor": None})
            elif len(parts) == 4:
                classes.append({"code": parts[0], "dept": parts[1], "course_num": parts[2], "instructor": parts[3]})
            else:
                print(
                    f"WARNING: Could not read this line in classes.txt (skipping it):\n"
                    f"  {line}\n"
                    f"  Expected either just a section code, or: code, dept, course number, instructor"
                )

    if not classes:
        print("ERROR: No valid classes found in classes.txt. Add at least one section code.")
        sys.exit(1)

    return classes


# ---------- selenium helpers ----------

def _make_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")  # recommended on Windows
    return webdriver.Chrome(options=options)


def _parse_enrollment(soup, section_code):
    """Find Max/Enr for the given section code in the results table. Returns (max, enr) or None."""
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if "Max" not in headers or "Enr" not in headers:
            continue
        max_idx = headers.index("Max")
        enr_idx = headers.index("Enr")
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if cells and cells[0].get_text(strip=True) == section_code:
                return cells[max_idx].get_text(strip=True), cells[enr_idx].get_text(strip=True)
    return None


# ---------- discord messaging ----------

def send_message(msg):
    requests.post(WEBHOOK_URL, json={"content": msg})

def _class_label(cls):
    if cls["course_num"] and cls["instructor"]:
        return f"{cls['course_num'].upper()} ({cls['code']})"
    return cls["code"]

def alert(cls, max_enroll, curr_enroll):
    label = _class_label(cls)
    send_message(f"**{label}** — spot opened! REGISTER NOW!\nMAX: {max_enroll}  CURR: {curr_enroll} <@{USER}>")

def sad_alert(cls, max_enroll, curr_enroll):
    label = _class_label(cls)
    send_message(f"**{label}** — no change. MAX: {max_enroll}  CURR: {curr_enroll}")

def record_and_alert(cls, max_enroll, curr_enroll):
    # Some classes show enrollment as "xx/yy" — yy is the effective cap for that section
    if "/" in curr_enroll:
        curr, effective_max = curr_enroll.split("/")
    else:
        curr, effective_max = curr_enroll, max_enroll

    label = _class_label(cls)
    print(f"  {label}: MAX={effective_max}  ENR={curr}")
    if curr != effective_max:
        alert(cls, effective_max, curr)
    else:
        sad_alert(cls, effective_max, curr)
    with open("current_vals.txt", "a") as f:
        f.write(f"{round(time.time())} : {cls['code']} : {effective_max} {curr}\n")


# ---------- startup validation ----------

def validate_classes(classes):
    print(f"\nMonitoring {len(classes)} class(es):")
    for cls in classes:
        if cls["dept"] and cls["course_num"] and cls["instructor"]:
            _validate_full(cls)
        else:
            print(f"  {cls['code']} — section-code-only mode (no validation)")
    print()

def _validate_full(cls):
    code, dept, course_num, instructor = cls["code"], cls["dept"], cls["course_num"], cls["instructor"]
    print(f"  {code} — checking it matches {course_num} / {instructor}...", end=" ", flush=True)

    driver = _make_driver()
    driver.get("https://www.reg.uci.edu/perl/WebSoc")
    Select(driver.find_element(By.NAME, "Dept")).select_by_visible_text(dept)
    time.sleep(0.1)
    driver.find_element(By.NAME, "CourseNum").send_keys(course_num)
    driver.find_element(By.NAME, "InstrName").send_keys(instructor)
    driver.find_element(By.XPATH, "//input[@type='submit' and @value='Display Web Results']").click()
    time.sleep(0.5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    result = _parse_enrollment(soup, code)
    if result is None:
        print(
            f"MISMATCH!\n"
            f"    Section {code} was NOT found under {dept} / {course_num} / {instructor}.\n"
            f"    Fix classes.txt and try again. Exiting."
        )
        sys.exit(1)

    print(f"OK (Max={result[0]}, Enr={result[1]})")


# ---------- main check loop ----------

def check_class(cls):
    driver = _make_driver()
    driver.get("https://www.reg.uci.edu/perl/WebSoc")
    driver.find_element(By.NAME, "CourseCodes").send_keys(cls["code"])
    driver.find_element(By.XPATH, "//input[@type='submit' and @value='Display Web Results']").click()
    time.sleep(0.5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    result = _parse_enrollment(soup, cls["code"])
    if result is None:
        print(f"  {cls['code']}: not found — check the section code and that the quarter is active.")
        return

    record_and_alert(cls, *result)


def GO():
    classes = load_classes()
    print(f"Checking {len(classes)} class(es)...")
    for cls in classes:
        check_class(cls)


def main():
    classes = load_classes()
    validate_classes(classes)
    open("current_vals.txt", "w").close()

    while True:
        print(f"Checking {len(classes)} class(es)...")
        for cls in classes:
            check_class(cls)
        time.sleep(TIME_CHECK)


if __name__ == "__main__":
    main()
