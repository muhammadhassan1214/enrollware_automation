from selenium.webdriver.common.by import By
from Utils.utils import *
import os
from dotenv import load_dotenv
from courses import AvailableCourses
import csv
from typing import Optional, Tuple, List, Dict, Any
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables and validate
load_dotenv()

# Validate required environment variables
REQUIRED_ENV_VARS = [
    "ENROLLWARE_USERNAME", "ENROLLWARE_PASSWORD",
    "ATLAS_USERNAME", "ATLAS_PASSWORD",
    "SHOP_CPR_USERNAME", "SHOP_CPR_PASSWORD", "SHOP_CPR_SECURITY_ID"
]

def validate_environment_variables() -> bool:
    """Validate that all required environment variables are set."""
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return False
    return True

# Initialize available courses with error handling
def get_available_courses():
    """Get available courses instance with error handling."""
    try:
        return AvailableCourses()
    except Exception as e:
        logger.error(f"Failed to initialize AvailableCourses: {e}")
        return None

available_courses = get_available_courses()


def login_to_enrollware_and_navigate_to_tc_product_orders(driver, max_retries: int = 3) -> bool:
    """Login to Enrollware and navigate to TC Product Orders with comprehensive error handling."""
    if not validate_environment_variables():
        return False

    for attempt in range(max_retries):
        try:
            if not safe_navigate_to_url(driver, "https://enrollware.com/admin"):
                continue

            time.sleep(5)

            # Check if already logged in
            validation_button = check_element_exists(driver, (By.ID, "loginButton"), timeout=5)

            if validation_button:
                # Input credentials with validation
                if not input_element(driver, (By.ID, "username"), os.getenv("ENROLLWARE_USERNAME")):
                    logger.error("Failed to input username")
                    continue

                if not input_element(driver, (By.ID, "password"), os.getenv("ENROLLWARE_PASSWORD")):
                    logger.error("Failed to input password")
                    continue

                # Optional remember me checkbox
                click_element_by_js(driver, (By.ID, "rememberMe"))
                time.sleep(1)

                if not click_element_by_js(driver, (By.ID, "loginButton")):
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


def navigate_to_tc_product_orders(driver, max_retries: int = 3) -> bool:
    """Navigate to TC Product Orders with error handling."""
    for attempt in range(max_retries):
        try:
            url = "https://www.enrollware.com/admin/tc-product-order-list-tc.aspx"
            if safe_navigate_to_url(driver, url):
                logger.info("Successfully navigated to TC Product Orders")
                return True
        except Exception as e:
            logger.error(f"Navigation attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue

    logger.error("Failed to navigate to TC Product Orders")
    return False


def login_to_ecards(driver, max_retries: int = 3) -> bool:
    """Login to eCards with comprehensive error handling and retry logic."""
    if not validate_environment_variables():
        return False

    for attempt in range(max_retries):
        try:
            # Check if already logged in
            if "https://ecards.heart.org/inventory" == driver.current_url:
                return True

            # Check for sign-in button
            sign_in_button = check_element_exists(driver, (By.XPATH, "(//button[text()= 'Sign In | Sign Up'])[1]"), timeout=5)
            email_field = check_element_exists(driver, (By.ID, "Email"), timeout=5)

            if sign_in_button and email_field:
                if not click_element_by_js(driver, (By.XPATH, "(//button[text()= 'Sign In | Sign Up'])[1]")):
                    continue

                time.sleep(3)

                # Check if redirected to inventory
                if "inventory" in driver.current_url:
                    return True

            # Proceed with login if email field exists
            if check_element_exists(driver, (By.ID, "Email"), timeout=5):
                if not input_element(driver, (By.ID, "Email"), os.getenv("ATLAS_USERNAME")):
                    continue

                time.sleep(2)

                if not input_element(driver, (By.ID, "Password"), os.getenv("ATLAS_PASSWORD")):
                    continue

                time.sleep(2)

                # Try to click remember me checkbox (optional)
                remember_me_xpath = "//input[@id= 'RememberMe']/following-sibling::label"
                if check_element_exists(driver, (By.XPATH, remember_me_xpath), timeout=3):
                    click_element_by_js(driver, (By.XPATH, remember_me_xpath))

                time.sleep(2)

                # Click sign-in button
                if not click_element_by_js(driver, (By.ID, "btnSignIn")):
                    continue

                time.sleep(5)

                # Verify login success
                if "https://ecards.heart.org/inventory" == driver.current_url:
                    return True
                else:
                    continue
            else:
                return True

        except:
            if attempt < max_retries - 1:
                time.sleep(3)
                continue

    logger.error("Failed to login to Atlas")
    return False


def navigate_to_eCard_section(driver, max_retries: int = 3, switch_timeout: float = 5.0) -> bool:
    """Navigate to eCard section, handling new tab opening and switching focus."""
    for attempt in range(max_retries):
        try:
            # Hover over Training Center
            if not move_to_element(driver, (By.XPATH, "//button[@id= 'Training Center']")):
                logger.error("Failed to hover over Training Center button")
                continue
            time.sleep(0.5)

            existing_handles = driver.window_handles[:]

            # Click eCards link (opens a new tab)
            if not click_element_by_js(driver, (By.XPATH, "//a[@title= 'eCards']")):
                logger.error("Failed to click eCards link")
                continue

            # Wait for a new window handle (if target=_blank)
            new_handle = None
            end_time = time.time() + switch_timeout
            while time.time() < end_time:
                current_handles = driver.window_handles
                if len(current_handles) > len(existing_handles):
                    diff = list(set(current_handles) - set(existing_handles))
                    if diff:
                        new_handle = diff[0]
                        break
                time.sleep(0.2)

            if new_handle:
                driver.switch_to.window(new_handle)
                logger.info("Switched to new eCards tab")
            else:
                logger.debug("No new tab detected; assuming same-tab navigation")

            # Verify navigation (URL or page content)
            for _ in range(20):  # up to ~10s
                url_ok = "Inventory" in driver.current_url.lower()
                marker = check_element_exists(
                    driver,
                    (By.XPATH, "//span[text()= 'eCard Inventory']"),
                    timeout=1
                )
                if url_ok or marker:
                    logger.info("Successfully navigated to eCard section")
                    return True
                time.sleep(0.5)

            logger.warning("eCard page verification not found; assuming success after click")
            return True

        except Exception as e:
            logger.error(f"eCard navigation attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)

    logger.error("Failed to navigate to eCard section")
    return False


def get_indexes_to_process(driver) -> List[int]:
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
                # Get text from columns safely
                td2_element = row.find_elements(By.XPATH, ".//td[2]")
                td2 = td2_element[0].text.strip().lower() if td2_element else ""

                td4_element = row.find_elements(By.XPATH, ".//td[4]")
                td4 = td4_element[0].text.strip().lower() if td4_element else ""

                # Exclusion conditions
                if "redcross" in td2 or "red cross" in td2:
                    continue

                if "complete" in td4 or "cancelled" in td4:
                    continue

                # If not excluded, keep index
                valid_indexes.append(i)

            except Exception as e:
                continue

        return valid_indexes

    except Exception as e:
        logger.error(f"Error getting indexes to process: {e}")
        return valid_indexes


def create_xpath(title: str) -> str:
    """Create XPath for order data extraction with validation."""
    if not title:
        logger.warning("Empty title provided for XPath creation")
        return ""
    return f"//label[text()= '{title}:']/parent::div/following-sibling::div"


def get_order_data(driver) -> Tuple[List[Dict[str, Any]], int]:
    """Get order data with comprehensive error handling and validation."""
    try:
        order_data = []

        # Get training site
        training_site_xpath = create_xpath('Training Site')
        training_site = get_element_text(driver, (By.XPATH, training_site_xpath), default="Unknown").strip()

        # Get name/address
        name_xpath = create_xpath('Name/Address')
        name = get_element_text(driver, (By.XPATH, name_xpath), default="Unknown")
        name = name.split('\n')[0].strip() if "\n" in name else name.strip()

        # Get number of orders
        products_xpath = f"{create_xpath('Products')}//tr"
        product_rows = driver.find_elements(By.XPATH, products_xpath)
        num_of_orders = max(0, len(product_rows) - 1)  # Subtract header row

        if num_of_orders == 0:
            return [], 0

        # Get order details
        quantity_elements = driver.find_elements(By.XPATH, f"{create_xpath('Products')}//td[1]")
        product_code_elements = driver.find_elements(By.XPATH, f"{create_xpath('Products')}//td[2]")
        course_name_elements = driver.find_elements(By.XPATH, f"{create_xpath('Products')}//td[3]")

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
                    "course_name": course_name
                })

            except Exception as e:
                continue

        return order_data, len(order_data)

    except Exception as e:
        logger.error(f"Critical error in get_order_data: {e}")
        return [], 0


def mark_order_as_complete(driver, max_retries: int = 3) -> bool:
    """Mark order as complete with comprehensive error handling."""
    for attempt in range(max_retries):
        try:
            # Select 'Complete' status
            if not select_by_text(driver, (By.ID, "mainContent_status"), 'Complete'):
                logger.error("Failed to select 'Complete' status")
                continue

            time.sleep(1)

            # Click status update button
            if not click_element_by_js(driver, (By.ID, "mainContent_statusUpdateBtn")):
                logger.error("Failed to click status update button")
                continue

            time.sleep(2)

            # Click email button
            if not click_element_by_js(driver, (By.ID, "mainContent_emailBtn")):
                logger.error("Failed to click email button")
                continue

            time.sleep(2)

            # Click send button
            if not click_element_by_js(driver, (By.ID, "mainContent_sendButton")):
                logger.error("Failed to click send button")
                continue

            time.sleep(2)

            # Click back button
            if not click_element_by_js(driver, (By.ID, "mainContent_backButton")):
                logger.error("Failed to click back button")
                continue

            logger.info("Successfully marked order as complete")
            return True

        except Exception as e:
            logger.error(f"Mark complete attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue

    logger.error("Failed to mark order as complete after all attempts")
    return False


def course_not_available(driver, product_code: str) -> bool:
    """Handle course not available scenario with error handling."""
    try:
        logger.warning(f"Course {product_code} is not available for eCard generation")

        # Go back and click back button
        go_back(driver)
        time.sleep(1)

        if click_element_by_js(driver, (By.ID, "mainContent_backButton")):
            logger.info("Successfully handled course not available scenario")
            return True
        else:
            logger.error("Failed to click back button in course_not_available")
            return False

    except Exception as e:
        logger.error(f"Error handling course not available: {e}")
        return False


def qyt_not_available(driver, product_code: str, available_qyt_on_ecard: int, quantity: int) -> bool:
    """Handle quantity not available scenario with error handling."""
    try:
        logger.warning(f"Quantity not available for {product_code}. Available: {available_qyt_on_ecard}, Requested: {quantity}")

        # Go back and click back button
        go_back(driver)
        time.sleep(1)

        if click_element_by_js(driver, (By.ID, "mainContent_backButton")):
            logger.info("Successfully handled quantity not available scenario")
            return True
        else:
            logger.error("Failed to click back button in qyt_not_available")
            return False

    except Exception as e:
        logger.error(f"Error handling quantity not available: {e}")
        return False


def go_back(driver, max_retries: int = 3) -> bool:
    """Go back by closing tabs with comprehensive error handling."""
    for attempt in range(max_retries):
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
            logger.error(f"Go back attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue

    logger.error("Failed to go back after all attempts")
    return False


def assign_to_instructor(driver, name: str, quantity: str, product_code: str, max_retries: int = 3) -> bool:
    """Assign to instructor with comprehensive error handling."""
    if not available_courses:
        logger.error("Available courses not initialized")
        return False

    for attempt in range(max_retries):
        try:
            time.sleep(2)

            # Click on the course
            available_course_selector = f"//td[contains(text(), '{product_code}')]/preceding-sibling::td[@role='button']"
            if not click_element_by_js(driver, (By.XPATH, available_course_selector)):
                continue

            time.sleep(2)

            # Click 'Assign to Instructor'
            if not click_element_by_js(driver, (By.XPATH, "//div/a[contains(text(), 'Assign to Instructor')]")):
                continue

            time.sleep(2)

            # Select TC Admin role
            if not select_by_text(driver, (By.ID, "RoleId"), 'TC Admin'):
                continue

            time.sleep(2)

            # Select course
            course_name_on_ecard = available_courses.course_name_on_eCard(product_code)
            if not course_name_on_ecard:
                logger.error(f"Course name not found for product code: {product_code}")
                continue

            if not select_by_text(driver, (By.ID, "CourseId"), course_name_on_ecard):
                continue

            time.sleep(2)

            # Select training center
            if not select_by_text(driver, (By.ID, "ddlTC"), 'Shell CPR, LLC.'):
                continue

            time.sleep(2)

            # Click assign to dropdown
            if not click_element_by_js(driver, (By.XPATH, "//select[@id= 'assignTo']/following-sibling::div/button")):
                continue

            time.sleep(2)

            # Select instructor by name
            instructor_xpath = f"(//label[contains(text(), '{name.title()}')])[1]"
            if not click_element_by_js(driver, (By.XPATH, instructor_xpath)):
                continue

            time.sleep(2)

            # Click move next
            if not click_element_by_js(driver, (By.ID, "btnMoveNext")):
                continue

            time.sleep(2)

            # Input quantity
            if not input_element(driver, (By.ID, "qty1"), str(quantity)):
                continue

            time.sleep(1)

            # Click confirm
            if not click_element_by_js(driver, (By.ID, "btnConfirm")):
                continue

            time.sleep(2)

            # Click complete
            if not click_element_by_js(driver, (By.ID, "btnComplete")):
                continue

            time.sleep(2)

            # Go to inventory
            if not click_element_by_js(driver, (By.XPATH, "//a[text()= 'Go To Inventory']")):
                continue

            logger.info(f"Successfully assigned {quantity} of {product_code} ({'Individual' if available_courses.is_individual_course(product_code) else 'Bundle'}) to instructor {name}")
            return True

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(3)
                continue

    logger.error("Failed to assign to instructor")
    return False


def assign_to_training_center(driver, quantity: str, product_code: str, training_site: str, max_retries: int = 3) -> bool:
    """Assign to training center with comprehensive error handling."""
    if not available_courses:
        logger.error("Available courses not initialized")
        return False

    # Check if this is appropriate for training site assignment
    if available_courses.is_individual_course(product_code):
        logger.info(f"Course {product_code} is an individual course - typically assigned to instructors, but proceeding with training site assignment as requested")

    for attempt in range(max_retries):
        try:
            # Click on the course
            available_course_selector = f"//td[contains(text(), '{product_code}')]/preceding-sibling::td[@role='button']"
            if not click_element_by_js(driver, (By.XPATH, available_course_selector)):
                continue

            time.sleep(2)

            # Click 'Assign to Training Site'
            if not click_element_by_js(driver, (By.XPATH, "//div/a[contains(text(), 'Assign to Training Site')]")):
                continue

            time.sleep(2)

            # Select training center
            if not select_by_text(driver, (By.ID, "tcId"), 'Shell CPR, LLC.'):
                continue

            time.sleep(2)

            # Select training site
            if not select_by_text(driver, (By.ID, "tsList"), training_site):
                continue

            time.sleep(2)

            # Select course
            course_name_on_ecard = available_courses.course_name_on_eCard(product_code)
            if not course_name_on_ecard:
                logger.error(f"Course name not found for product code: {product_code}")
                continue

            if not select_by_text(driver, (By.ID, "courseId"), course_name_on_ecard):
                continue

            time.sleep(2)

            # Input quantity
            if not input_element(driver, (By.ID, "qty"), str(quantity)):
                continue

            # Click validate
            if not click_element_by_js(driver, (By.ID, "btnValidate")):
                continue

            time.sleep(2)

            # Click complete
            if not click_element_by_js(driver, (By.ID, "btnComplete")):
                continue

            time.sleep(2)

            # Go to inventory
            if not click_element_by_js(driver, (By.XPATH, "//a[text()= 'Go To Inventory']")):
                continue

            logger.info(f"Successfully assigned {quantity} of {product_code} ({'Individual' if available_courses.is_individual_course(product_code) else 'Bundle'}) to training site {training_site}")
            return True

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(3)
                continue

    logger.error("Failed to assign to training center after all attempts")
    return False


def get_training_site_name(code: str) -> Optional[str]:
    """Get training site name from CSV with comprehensive error handling."""
    if not code:
        logger.warning("Empty code provided for training site lookup")
        return None

    csv_path = os.path.join('Utils', 'training_sites.csv')

    try:
        if not os.path.exists(csv_path):
            logger.error(f"Training sites CSV file not found: {csv_path}")
            return None

        with open(csv_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row_num, row in enumerate(reader, start=2):  # Start at 2 because of header
                try:
                    if row.get('Code', '').strip() == code.strip():
                        training_site_name = row.get('Text', '').strip()
                        if training_site_name:
                            logger.info(f"Found training site: {code} -> {training_site_name}")
                            return training_site_name
                        else:
                            logger.warning(f"Empty training site name for code: {code}")
                            return None
                except Exception as e:
                    logger.error(f"Error processing CSV row {row_num}: {e}")
                    continue

        logger.warning(f"Training site code not found: {code}")
        return None

    except FileNotFoundError:
        logger.error(f"Training sites CSV file not found: {csv_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading training sites CSV: {e}")
        return None


def login_to_shop_cpr(driver, max_retries: int = 3) -> bool:
    """Login to ShopCPR with comprehensive error handling."""
    if not validate_environment_variables():
        return False

    for attempt in range(max_retries):
        try:
            if not safe_navigate_to_url(driver, "https://shopcpr.heart.org/"):
                continue

            time.sleep(5)

            # Check if already logged in
            sign_in_btn = check_element_exists(driver, (By.XPATH, "//a[contains(@href, 'login')]"), timeout=5)

            if sign_in_btn:
                logger.info("Logging into ShopCPR")

                if not click_element_by_js(driver, (By.XPATH, "//a[contains(@href, 'login')]")):
                    logger.error("Failed to click sign-in link")
                    continue

                time.sleep(3)

                # Input credentials
                if not input_element(driver, (By.ID, "Email"), os.getenv("SHOP_CPR_USERNAME")):
                    logger.error("Failed to input ShopCPR email")
                    continue

                time.sleep(2)

                if not input_element(driver, (By.ID, "Password"), os.getenv("SHOP_CPR_PASSWORD")):
                    logger.error("Failed to input ShopCPR password")
                    continue

                time.sleep(2)

                if not click_element_by_js(driver, (By.ID, "btnSignIn")):
                    logger.error("Failed to click ShopCPR sign-in button")
                    continue

                time.sleep(5)

                # Verify login success
                if "account" in driver.current_url.lower() or not check_element_exists(driver, (By.XPATH, "//a[contains(@href, 'login')]"), timeout=3):
                    logger.info("Successfully logged into ShopCPR")
                    return True
                else:
                    logger.warning("ShopCPR login verification failed")
                    continue
            else:
                logger.info("Already logged into ShopCPR")
                return True

        except Exception as e:
            logger.error(f"ShopCPR login attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(3)
                continue

    logger.error("Failed to login to ShopCPR after all attempts")
    return False


def checkout_popup_handling(driver) -> bool:
    """Handle checkout popup with error handling."""
    try:
        popup = check_element_exists(driver, (By.XPATH, "//div[@id= 'org-form']"), timeout=5)
        if popup:
            logger.info("Handling checkout popup")
            if click_element_by_js(driver, (By.XPATH, "//button[text()= 'Continue']")):
                time.sleep(2)
                logger.info("Successfully handled checkout popup")
                return True
            else:
                logger.error("Failed to click continue button in popup")
                return False
        else:
            logger.info("No checkout popup found")
            return True
    except Exception as e:
        logger.error(f"Error handling checkout popup: {e}")
        return False


def clear_cart_on_shop_cpr(driver, max_retries: int = 2) -> bool:
    """Clear cart on ShopCPR with comprehensive error handling."""
    if not validate_environment_variables():
        return False

    for attempt in range(max_retries):
        try:
            # Check if cart is empty
            cart_count = get_element_text(driver, (By.CLASS_NAME, "scpr-cartcount"), timeout=3)
            cart_count = cart_count.replace("(", "").replace(")", "").strip() if "(" in cart_count else cart_count.strip()
            logger.info(f"Cart: {cart_count}")
            if int(cart_count) == 0:
                logger.info("Cart is already empty")
                return True


            # Navigate to cart
            if not click_element_by_js(driver, (By.ID, "aha-showcart")):
                logger.error("Failed to click show cart")
                continue

            time.sleep(2)

            # Click delete buttons
            delete_buttons = driver.find_elements(By.XPATH, "//a[contains(@id, 'delete-item')]")
            for btn in delete_buttons:
                try:
                    btn.click()
                    time.sleep(1)
                    click_element_by_js(driver, (By.ID, "remove-product"))
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Failed to click delete button: {e}")
                    continue

            time.sleep(2)

            # Verify cart is empty
            empty_cart_msg = check_element_exists(driver, (By.XPATH, "//p[contains(text(), 'You have no items in your shopping cart.')]"), timeout=5)
            if empty_cart_msg:
                logger.info("Successfully cleared the cart")
                return True
            else:
                logger.error("Cart not empty after clearing attempt")
                continue

        except Exception as e:
            logger.error(f"Clear cart attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(3)
                continue

    logger.error("Failed to clear cart after all attempts")
    return False

def make_purchase_on_shop_cpr(driver, product_code: str, quantity_to_order: int, name: str, max_retries: int = 2) -> bool:
    """Make purchase on ShopCPR with comprehensive error handling."""
    if not validate_environment_variables():
        return False

    is_individual = available_courses.is_individual_course(product_code) if available_courses else False
    original_window = driver.current_window_handle

    for attempt in range(max_retries):
        try:
            # Open new tab
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])

            # Login to ShopCPR
            if not login_to_shop_cpr(driver):
                logger.error("Failed to login to ShopCPR for purchase")
                continue

            # Clear cart
            if not clear_cart_on_shop_cpr(driver):
                logger.error("Failed to clear cart before purchase")
                continue

            # Navigate to Course Cards
            if not click_element_by_js(driver, (By.XPATH, "//span[text()= 'Course Cards']/parent::a")):
                logger.error("Failed to click Course Cards")
                continue

            time.sleep(2)

            # Navigate to Heartsaver Bundles
            if not click_element_by_js(driver, (By.XPATH, "//span[text()= 'Heartsaver Bundles']/parent::a")):
                logger.error("Failed to click Heartsaver Bundles")
                continue

            time.sleep(3)

            # Click search button
            if not click_element_by_js(driver, (By.XPATH, "//button[@title= 'Search Product']")):
                logger.error("Failed to click search button")
                continue

            time.sleep(2)

            # Search for product
            if not input_element(driver, (By.XPATH, "//input[@id= 'searchtext']"), product_code):
                logger.error("Failed to input product code for search")
                continue

            time.sleep(1)

            if not click_element_by_js(driver, (By.XPATH, "//button[@id= 'btnsearch']")):
                logger.error("Failed to click search button")
                continue

            time.sleep(3)

            if not is_individual:
                if not click_element_by_js(driver, (By.XPATH, "//a[@title= 'View Details']")):
                    logger.error("Failed to click View Details for bundle")
                    continue

                time.sleep(2)

                if not click_element_by_js(driver, (By.XPATH, "//button[@id= 'bundle-slide']")):
                    logger.error("Failed to click Add to Cart for bundle")
                    continue

            # Input quantity
            if not input_element(driver, (By.XPATH, "//input[@id= 'qty']"), str(quantity_to_order)):
                logger.error("Failed to input quantity")
                continue

            time.sleep(1)

            # Add to cart
            if not click_element_by_js(driver, (By.XPATH, "//button[@id= 'product-addtocart-button']")):
                logger.error("Failed to add to cart")
                continue

            time.sleep(3)

            # Show cart
            if not click_element_by_js(driver, (By.XPATH, "//a[@id= 'aha-showcart']")):
                logger.error("Failed to show cart")
                continue

            time.sleep(2)

            # Checkout
            if not click_element_by_js(driver, (By.ID, "top-cart-btn-checkout")):
                logger.error("Failed to click checkout")
                continue

            time.sleep(3)

            # Handle popup
            checkout_popup_handling(driver)
            time.sleep(2)

            # Input security ID
            security_id = os.getenv("SHOP_CPR_SECURITY_ID")
            if not input_element(driver, (By.XPATH, "//input[@id= 'sid']"), security_id):
                logger.error("Failed to input security ID")
                continue

            time.sleep(1)

            # Proceed to checkout
            if not click_element_by_js(driver, (By.ID, "proceed-checkout")):
                logger.error("Failed to proceed to checkout")
                continue

            time.sleep(3)

            if not is_individual: # If the order is a bundle
                if not click_element_by_js(driver, (By.ID, "taxStatus")):
                    logger.error("Failed to click purchase code")
                    continue

                time.sleep(1)
                training_site_name = get_training_site_name(product_code)
                is_training_site_availabel = check_element_exists(driver, (By.XPATH, f"//a[contains(text(), '{training_site_name}')]"))

                if is_training_site_availabel:
                    if not click_element_by_js(driver, (By.XPATH, f"//a[contains(text(), '{training_site_name}')]")):
                        logger.error("Failed to select training site")
                        continue
                else:
                    if not click_element_by_js(driver, (By.XPATH, "//a[contains(text(), '3SLHD-619865-Shell CPR')]")):
                        logger.error("Failed to select purchase code")
                        continue

                time.sleep(1)

                if not click_element_by_js(driver, (By.ID, "purchase-continue-btn")):
                    logger.error("Failed to apply purchase code")
                    continue

                time.sleep(1)

            # Input PO number
            if not input_element(driver, (By.ID, "po_number"), name):
                logger.error("Failed to input PO number")
                continue

            time.sleep(1)

            # Proceed to payment
            if not click_element_by_js(driver, (By.XPATH, "//button[text()= 'Proceed to Payment']")):
                logger.error("Failed to proceed to payment")
                continue

            time.sleep(5)

            # Check order confirmation
            if "orderconfirmation" in driver.current_url:
                logger.info(f"Successfully purchased {quantity_to_order} of {product_code} eCards for {name}")

                # Close tab and return to original
                driver.close()
                driver.switch_to.window(original_window)
                time.sleep(2)
                driver.refresh()
                return True
            else:
                logger.error(f"Purchase failed - not on confirmation page. Current URL: {driver.current_url}")
                continue

        except Exception as e:
            logger.error(f"Purchase attempt {attempt + 1} failed: {e}")

            # Cleanup on error
            try:
                if len(driver.window_handles) > 1:
                    driver.close()
                if driver.window_handles:
                    driver.switch_to.window(original_window)
            except:
                pass

            if attempt < max_retries - 1:
                time.sleep(3)
                continue

    logger.error(f"Failed to complete purchase for {product_code} after all attempts")
    return False
