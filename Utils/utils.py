from selenium import webdriver
import time
import os
from selenium.webdriver import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.select import Select

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def click_element(driver, by_locator):
    element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(by_locator))
    driver.execute_script(
        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'nearest'})", element)
    element.click()


def click_element_by_js(driver, by_locator):
    element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(by_locator))
    driver.execute_script(
        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'nearest'})", element)
    driver.execute_script("arguments[0].click();", element)
    time.sleep(0.5)


def input_element(driver, by_locator, text):
    element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(by_locator))
    driver.execute_script(
        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'nearest'})", element)
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located(by_locator)).send_keys(Keys.CONTROL, '\A',
                                                                                            '\b')
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located(by_locator)).send_keys(text)


def move_to_element(driver, locator):
    element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located(locator))
    actions = ActionChains(driver)
    actions.move_to_element(element).perform()


def get_element_text(driver, by_locator):
    element = WebDriverWait(driver, 40).until(EC.visibility_of_element_located(by_locator))
    return element.text.strip()

def get_undetected_driver(headless=False, max_retries=3):
    try:
        options = webdriver.ChromeOptions()
        path = rf'{BASE_DIR}\chrome-dir'
        options.add_argument(f'--user-data-dir={path}')
        options.add_argument("--log-level=3")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")

        if not headless:
            options.add_argument("--start-maximized")
        else:
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")

        # Initialize undetected Chrome driver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        time.sleep(2)  # Allow the browser to fully initialize

        # Additional fingerprinting tweaks (remove WebDriver flag)
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        return driver

    except Exception as e:
        print(f"Error: {e}")
        if max_retries > 0:
            print(f"Retrying... Attempts left: {max_retries}")
            time.sleep(2)
            return get_undetected_driver(headless=headless, max_retries=max_retries - 1)
        else:
            print("Max retries exceeded. Could not create the driver.")
            return None

def check_element_exists(driver, by_locator):
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located(by_locator))
        return True
    except:
        return False

def select_by_text(driver, by_locator, text):
    select_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(by_locator))
    select = Select(select_element)
    select.select_by_visible_text(text)