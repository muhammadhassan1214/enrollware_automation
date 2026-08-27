import os
import time
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from typing import Tuple, List, Dict, Any
from Utils.functions import validate_environment_variables, logger
from Utils.pageSelectors import EnrollwareLoginPage, EnrollwareOrderPage
from Utils.utils import (
    input_element, select_by_text,
    get_element_text, check_element_exists,
    click_element_by_js, safe_navigate_to_url
)

load_dotenv()

def login_to_enrollware_and_navigate_to_tc_product_orders(driver, max_retries: int = 3) -> bool:
    """Login to Enrollware and navigate to TC Product Orders with comprehensive error handling."""
    if not validate_environment_variables():
        return False

    for attempt in range(max_retries):
        try:
            if not safe_navigate_to_url(driver, "https://www.enrollware.com/admin/login.aspx?"):
                continue

            time.sleep(5)

            # Check if already logged in
            validation_button = check_element_exists(driver, EnrollwareLoginPage.login_button, timeout=5)

            if validation_button:
                # Input credentials with validation
                if not input_element(driver, EnrollwareLoginPage.username_input, os.getenv("ENROLLWARE_USERNAME")):
                    logger.error("Failed to input username")
                    continue

                if not input_element(driver, EnrollwareLoginPage.password_input, os.getenv("ENROLLWARE_PASSWORD")):
                    logger.error("Failed to input password")
                    continue

                # Optional remember me checkbox
                click_element_by_js(driver, EnrollwareLoginPage.remember_me_checkbox)
                time.sleep(1)

                if not click_element_by_js(driver, EnrollwareLoginPage.login_button):
                    logger.error("Failed to click login button")
                    continue

                # Wait for login to complete
                time.sleep(20)

                # Verify login success
                if "admin" in driver.current_url.lower():
                    logger.info("Successfully logged into Enrollware")
                else:
                    logger.warning("Login may have failed, checking current URL")
                    continue

            # Navigate to TC Product Orders
            return navigate_to_tc_product_orders(driver)

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(3)
                continue

    logger.error("Failed to login to Enrollware after all attempts")
    return False


def navigate_to_tc_product_orders(driver) -> bool:
    """Navigate to TC Product Orders with error handling."""
    try:
        url = "https://www.enrollware.com/admin/tc-product-order-list-tc.aspx"
        if safe_navigate_to_url(driver, url):
            logger.info("Successfully navigated to TC Product Orders")
            return True
    except Exception as e:
        logger.error(f"Navigation failed: {e}")
        return False


def get_indexes_to_process(driver, condition) -> List[int]:
    """Get valid row indexes to process with comprehensive error handling."""
    valid_indexes = []

    try:
        # Wait for table to load
        if not check_element_exists(driver, (By.XPATH, "//tbody/tr"), timeout=10):
            logger.warning("No table rows found")
            return valid_indexes

        # Find all rows inside the table
        rows = driver.find_elements(By.XPATH, "//tbody/tr")

        for i, row in enumerate(rows, start=1):  # start=1 for 1-based index
            try:
                # Paid Status check
                td5_element = row.find_elements(By.XPATH, ".//td[3]")
                td5 = td5_element[0].text.strip().lower() if td5_element else ""
                if "no" in td5:
                    continue

                # Get text from columns safely
                td2_element = row.find_elements(By.XPATH, ".//td[2]")
                td2 = td2_element[0].text.strip().lower() if td2_element else ""

                td4_element = row.find_elements(By.XPATH, ".//td[4]")
                td4 = td4_element[0].text.strip().lower() if td4_element else ""

                if condition == "redcross":
                    # Inclusion conditions for Red Cross
                    if "redcross" not in td2 and "red cross" not in td2:
                        continue

                    if "complete" in td4 or "cancelled" in td4:
                        continue

                elif condition == "non-redcross":
                    # Exclusion conditions
                    if "redcross" in td2 or "red cross" in td2:
                        continue

                    if "complete" in td4 or "cancelled" in td4:
                        continue

                else:
                    logger.error(f"Unknown condition: {condition}")
                    return valid_indexes

                # If not excluded, keep index
                valid_indexes.append(i)

            except:
                continue

        return valid_indexes

    except Exception as e:
        logger.error(f"Error getting indexes to process: {e}")
        return valid_indexes


def get_order_data(driver) -> Tuple[List[Dict[str, Any]], int]:
    """Get order data with comprehensive error handling and validation."""
    try:
        order_data = []

        # Get training site
        training_site_xpath = EnrollwareOrderPage.order_data('Training Site')
        training_site = get_element_text(driver, (By.XPATH, training_site_xpath), default="Unknown").strip()

        # Get name/address
        name_xpath = EnrollwareOrderPage.order_data('Name/Address')
        name = get_element_text(driver, (By.XPATH, name_xpath), default="Unknown")
        name = name.split('\n')[0].strip() if "\n" in name else name.strip()

        # Get Email Address
        email_xpath = EnrollwareOrderPage.order_data('Email Address')
        email = get_element_text(driver, (By.XPATH, email_xpath), default="").strip()

        # Get number of orders
        products_xpath = f"{EnrollwareOrderPage.order_data('Products')}//tr"
        product_rows = driver.find_elements(By.XPATH, products_xpath)
        num_of_orders = max(0, len(product_rows) - 1)  # Subtract header row

        if num_of_orders == 0:
            return [], 0

        # Get order details
        quantity_elements = driver.find_elements(By.XPATH, f"{EnrollwareOrderPage.order_data('Products')}//td[1]")
        product_code_elements = driver.find_elements(By.XPATH, f"{EnrollwareOrderPage.order_data('Products')}//td[2]")
        course_name_elements = driver.find_elements(By.XPATH, f"{EnrollwareOrderPage.order_data('Products')}//td[3]")

        # Validate element counts
        min_count = min(len(quantity_elements), len(product_code_elements), len(course_name_elements))
        if min_count < num_of_orders:
            num_of_orders = min_count

        # Extract order data
        for i in range(num_of_orders):
            try:
                quantity = quantity_elements[i].text.strip() if i < len(quantity_elements) else ""
                product_code = product_code_elements[i].text.strip() if i < len(product_code_elements) else ""
                course_name = course_name_elements[i].text.strip() if i < len(course_name_elements) else ""

                # Validate required fields
                if not all([quantity, product_code, course_name]):
                    continue

                order_data.append({
                    "training_site": training_site,
                    "name": name,
                    "quantity": quantity,
                    "product_code": product_code,
                    "course_name": course_name,
                    "email": email
                })

            except Exception as e:
                continue

        return order_data, len(order_data)

    except Exception as e:
        logger.error(f"Critical error in get_order_data: {e}")
        return [], 0


def mark_order_as_complete(driver) -> bool:
    """Mark order as complete with comprehensive error handling."""
    try:
        # Select 'Complete' status
        if not select_by_text(driver, EnrollwareOrderPage.order_status_select, 'Complete'):
            logger.error("Failed to select 'Complete' status")
            return False

        # Click status update button
        if not click_element_by_js(driver, EnrollwareOrderPage.status_update_button):
            logger.error("Failed to click status update button")
            return False

        time.sleep(2)

        # Click email button
        if not click_element_by_js(driver, EnrollwareOrderPage.email_button):
            logger.error("Failed to click email button")
            return False

        time.sleep(1)

        # Click send button
        if not click_element_by_js(driver, EnrollwareOrderPage.send_email_button):
            logger.error("Failed to click send button")
            return False

        time.sleep(1)

        # Click back button
        if not click_element_by_js(driver, EnrollwareOrderPage.back_button):
            logger.error("Failed to click back button")
            return False

        logger.info("Successfully marked order as complete")
        return True

    except Exception as e:
        logger.error(f"Mark complete attempt failed: {e}")
        return False


def go_back(driver) -> bool:
    """Go back by closing tabs with comprehensive error handling."""
    try:
        initial_handles = len(driver.window_handles)

        if initial_handles > 1:
            # Close current tab
            driver.close()
            time.sleep(1)

            # Switch to the last remaining window
            remaining_handles = driver.window_handles
            if remaining_handles:
                driver.switch_to.window(remaining_handles[-1])
                time.sleep(1)

                # If still multiple tabs, close one more
                if len(remaining_handles) > 1:
                    driver.close()
                    time.sleep(1)

                    # Switch to the first window
                    final_handles = driver.window_handles
                    if final_handles:
                        driver.switch_to.window(final_handles[0])
                        time.sleep(1)

                logger.info("Successfully navigated back by closing tabs")
                return True
            else:
                logger.error("No window handles remaining after closing")
                return False
        else:
            logger.info("Only one window handle, no need to go back")
            return True

    except Exception as e:
        logger.error(f"Go back attempt failed: {e}")
        time.sleep(2)
        return False