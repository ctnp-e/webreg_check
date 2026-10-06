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

def _parse_class_line(line):
    """
    Parse one non-comment line from classes.txt. Returns a class dict or None.

    Supported formats:
      1 part  — section code only:           34210
      3 parts — dept, course, instructor:    COMPSCI..., 164, eppstein
      4 parts — code + full info:            34210, COMPSCI..., 164, eppstein
    """
    parts = [p.strip() for p in line.split(",")]

    if len(parts) == 1:
        return {"code": parts[0], "dept": None, "course_num": None, "instructor": None, "title": None}
    elif len(parts) == 3:
        return {"code": None, "dept": parts[0], "course_num": parts[1], "instructor": parts[2], "title": None}
    elif len(parts) == 4:
        return {"code": parts[0], "dept": parts[1], "course_num": parts[2], "instructor": parts[3], "title": None}
    return None


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
            cls = _parse_class_line(line)
            if cls is None:
                print(
                    f"WARNING: Could not read this line in classes.txt (skipping it):\n"
                    f"  {line}\n"
                    f"  Expected: section_code  OR  dept, course_num, instructor  "
                    f"OR  section_code, dept, course_num, instructor"
                )
            else:
                classes.append(cls)

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
    """Find Max/Enr for one section code. Returns (max, enr) or None."""
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


def _parse_all_enrollments(soup):
    """Find every section row in the results table. Returns list of (code, max, enr)."""
    results = []
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if "Max" not in headers or "Enr" not in headers:
            continue
        max_idx = headers.index("Max")
        enr_idx = headers.index("Enr")
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if not cells:
                continue
            code = cells[0].get_text(strip=True)
            if code.isdigit():
                results.append((
                    code,
                    cells[max_idx].get_text(strip=True),
                    cells[enr_idx].get_text(strip=True),
                ))
    return results


def _parse_course_title(soup, section_code):
    """
    Find the course title shown above a section row in the WebSOC results.
    WebSOC prints a spanning title row (e.g. 'COMPSCI 162. FORMAL LANGUAGES...')
    before each group of sections. We walk rows and remember the last title seen.
    """
    for table in soup.find_all("table"):
        last_title = None
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if not cells:
                continue
            first = cells[0]
            colspan = int(first.get("colspan", 1))
            if colspan > 3:
                raw = first.get_text(strip=True)
                last_title = raw.split("(")[0].strip()
            elif first.get_text(strip=True) == section_code:
                return last_title
    return None


# ---------- discord messaging ----------

def send_message(msg):
    requests.post(WEBHOOK_URL, json={"content": msg})

def _class_label(cls):
    title = cls.get("title")
    code  = cls.get("code")
    if title:
        code_part = f" ({code})" if code else ""
        return f"{title}{code_part}"
    if cls.get("course_num") and cls.get("instructor"):
        code_part = f" ({code})" if code else ""
        return f"{cls['course_num'].upper()}{code_part}"
    return code or "unknown"

def alert(cls, max_enroll, curr_enroll):
    send_message(f"**{_class_label(cls)}** — spot opened! REGISTER NOW!\nMAX: {max_enroll}  CURR: {curr_enroll} <@{USER}>")

def sad_alert(cls, max_enroll, curr_enroll):
    send_message(f"**{_class_label(cls)}** — no change. MAX: {max_enroll}  CURR: {curr_enroll}")

def record_and_alert(cls, max_enroll, curr_enroll):
    # Some classes show enrollment as "xx/yy" — yy is the effective cap for that section
    if "/" in curr_enroll:
        curr, effective_max = [x.strip() for x in curr_enroll.split("/")]
    else:
        curr, effective_max = curr_enroll, max_enroll

    print(f"  {_class_label(cls)}: MAX={effective_max}  ENR={curr}")
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
        if cls["code"] is None:
            print(f"  {cls['course_num']} / {cls['instructor']} — will find all sections at runtime")
        elif cls["dept"] and cls["course_num"] and cls["instructor"]:
            _validate_full(cls)
        else:
            print(f"  {cls['code']} — section-code-only mode (no validation)")
    print()

def _validate_full(cls):
    code = cls["code"]
    print(f"  {code} — checking it matches {cls['course_num']} / {cls['instructor']}...", end=" ", flush=True)

    driver = _make_driver()
    driver.get("https://www.reg.uci.edu/perl/WebSoc")
    Select(driver.find_element(By.NAME, "Dept")).select_by_visible_text(cls["dept"])
    time.sleep(0.1)
    driver.find_element(By.NAME, "CourseNum").send_keys(cls["course_num"])
    driver.find_element(By.NAME, "InstrName").send_keys(cls["instructor"])
    driver.find_element(By.XPATH, "//input[@type='submit' and @value='Display Web Results']").click()
    time.sleep(0.5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    result = _parse_enrollment(soup, code)
    if result is None:
        print(
            f"MISMATCH!\n"
            f"    Section {code} was NOT found under "
            f"{cls['dept']} / {cls['course_num']} / {cls['instructor']}.\n"
            f"    Fix classes.txt and try again. Exiting."
        )
        sys.exit(1)

    print(f"OK (Max={result[0]}, Enr={result[1]})")


# ---------- main check loop ----------

def check_class(cls):
    driver = _make_driver()
    driver.get("https://www.reg.uci.edu/perl/WebSoc")

    if cls["code"] is None:
        # No section code — search by class info and watch every section found
        Select(driver.find_element(By.NAME, "Dept")).select_by_visible_text(cls["dept"])
        time.sleep(0.1)
        driver.find_element(By.NAME, "CourseNum").send_keys(cls["course_num"])
        driver.find_element(By.NAME, "InstrName").send_keys(cls["instructor"])
    else:
        driver.find_element(By.NAME, "CourseCodes").send_keys(cls["code"])

    driver.find_element(By.XPATH, "//input[@type='submit' and @value='Display Web Results']").click()
    time.sleep(0.5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    if cls["code"] is None:
        sections = _parse_all_enrollments(soup)
        if not sections:
            print(f"  No sections found for {cls['course_num']} / {cls['instructor']} — check the quarter is active.")
            return
        for code, max_enroll, curr_enroll in sections:
            section_cls = {**cls, "code": code, "title": _parse_course_title(soup, code)}
            record_and_alert(section_cls, max_enroll, curr_enroll)
    else:
        result = _parse_enrollment(soup, cls["code"])
        if result is None:
            print(f"  {cls['code']}: not found — check the section code and that the quarter is active.")
            return
        enriched = {**cls, "title": _parse_course_title(soup, cls["code"])}
        record_and_alert(enriched, *result)


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
