from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Opens Chrome
driver = webdriver.Chrome()

driver.get("https://www.google.com")

time.sleep(3)

print(driver.find_element(By.TAG_NAME, "body").text)

driver.quit()