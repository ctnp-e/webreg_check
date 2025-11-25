from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time

# Configure your driver (Chrome in this example)
driver = webdriver.Chrome()

# Load WebSOC page
driver.get("https://www.reg.uci.edu/perl/WebSoc")

# # 1. Select the quarter/term drop-down
# term_dropdown = Select(driver.find_element(By.NAME, "YearTerm"))  # example name
# term_dropdown.select_by_visible_text("2025 Fall Quarter")         # adjust as needed
# time.sleep(1)  # wait for any reload

# 2. Select department drop-down
dept_dropdown = Select(driver.find_element(By.NAME, "Dept")) 
dept_dropdown.select_by_visible_text("COMPSCI . . . . Computer Science")
time.sleep(1)

# 3. Submit search
driver.find_element(By.XPATH, "//input[@type='submit' and @value='Display Text Results']").click()
time.sleep(2)  # wait for results to load


driver.quit()
