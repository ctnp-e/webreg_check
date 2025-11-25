from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time

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


