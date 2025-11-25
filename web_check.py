import requests
from bs4 import BeautifulSoup
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time


with open("webhook_val.txt", "r") as f:
    data = f.read().strip()
    WEBHOOK_URL = data

# WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_HERE"
LAST_VALUE_FILE = "lastvalue.txt"
TIME_CHECK = 120 #seconds





def add_to_curr_vals(particular_inp) :
    result = particular_inp.strip().split(" ")
    result = [x for x in result if x.strip()]

    # ohyea = 0
    # for line in result:
    #     print(str(ohyea) + " : " + line)
    #     ohyea += 1
    
    total_len = len(result)
    max = result[total_len-6]
    curr = result[total_len-5]
    if (curr != max) :
        alert()

    print_to_curr_vals( max + " " + curr)


def print_to_curr_vals(line) :
    with open("current_vals.txt", "a") as f:
        f.write(str(round(time.time())) + " : " + line + "\n")
    


def GO() :

    driver = webdriver.Chrome()
    driver.get("https://www.reg.uci.edu/perl/WebSoc") # loads WebSOC page

    # select dept via drop down
    # TODO : make dict to select from terminal
    dept_dropdown = Select(driver.find_element(By.NAME, "Dept")) 
    dept_dropdown.select_by_visible_text("COMPSCI . . . . Computer Science")
    time.sleep(0.1)

    # select particular course num
    # TODO : make this optional
    input_box = driver.find_element(By.NAME, "CourseNum")
    input_box.send_keys("142a")

    # select particular instructor
    # TODO : make this optional
    input_box = driver.find_element(By.NAME, "InstrName")
    input_box.send_keys("demsky")


    driver.find_element(By.XPATH, "//input[@type='submit' and @value='Display Text Results']").click()
    time.sleep(0.5)  # wait for results to load

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    particular_inp = ""
    # finds exact course
    text = soup.get_text(separator="\n", strip=True)
    for line in text.splitlines():
        if "34130" in line :
            add_to_curr_vals(line)
    
    
    driver.quit()


def main():

    open('current_vals.txt', 'w').close()
    
    while True:
        GO()
        time.sleep(10)


main()

