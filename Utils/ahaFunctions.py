import os
import re
import time
from dotenv import load_dotenv
from Utils.pageSelectors import AHALoginPage, AHAInventoryPage, AssignToInstructorPage, AssignToTrainingCenterPage
from selenium.webdriver.common.by import By
from Utils.functions import validate_environment_variables, logger, get_available_courses
from Utils.utils import (
    input_element, select_by_text, move_to_element,
    get_element_text, check_element_exists,
    click_element_by_js, safe_navigate_to_url
)

load_dotenv()
available_courses = get_available_courses()


def login_to_ecards(driver, username=os.getenv("ATLAS_USERNAME"), password=os.getenv("ATLAS_PASSWORD")) -> bool:
    """Login to eCards with comprehensive error handling and retry logic."""
    other_account = check_element_exists(driver, (By.XPATH, "//label[text()= 'Training Site']"), timeout=3)
    if other_account:
        logout_from_aha(driver)
    if not validate_environment_variables():
        return False
    try:
        # Check if already logged in
        if "https://ecards.heart.org/inventory" == driver.current_url:
            return True

        # Check for sign-in button
        sign_in_button = check_element_exists(driver, AHALoginPage.sign_in_link, timeout=3)


        if sign_in_button:
            if not click_element_by_js(driver, AHALoginPage.sign_in_link):
                return False

            time.sleep(3)

            # Check if redirected to inventory
            if "inventory" in driver.current_url:
                return True

        # Proceed with login if email field exists
        if check_element_exists(driver, AHALoginPage.username_input, timeout=5):
            if not input_element(driver, AHALoginPage.username_input, username):
                return False

            time.sleep(1)

            if not input_element(driver, AHALoginPage.password_input, password):
                return False

            time.sleep(1)

            # Try to click remember me checkbox (optional)
            # remember_me_xpath = "//input[@id= 'RememberMe']/following-sibling::label"
            # if check_element_exists(driver, (By.XPATH, remember_me_xpath), timeout=3):
            #     click_element_by_js(driver, (By.XPATH, remember_me_xpath))
            #
            # time.sleep(1)

            # Click sign-in button
            if not click_element_by_js(driver, AHALoginPage.sign_in_button):
                return False

            time.sleep(5)

            # Verify login success
            if "https://ecards.heart.org/inventory" == driver.current_url:
                return True
            else:
                return False
        else:
            return True

    except:
        logger.error("Failed to login to Atlas")
        return False


def assign_to_instructor(driver, name: str, quantity: str, product_code: str) -> bool:
    """Assign to instructor with comprehensive error handling."""
    if not available_courses:
        logger.error("Available courses not initialized")
        return False

    try:
        # Click on the course
        if not click_element_by_js(driver, f"{AHAInventoryPage.available_course_selector(product_code)}[@role='button']"):
            return False

        time.sleep(1)

        # Click 'Assign to Instructor'
        if not click_element_by_js(driver, AHAInventoryPage.assign_to('Instructor')):
            return False

        time.sleep(2)

        # Select TC Admin role
        if not select_by_text(driver, AssignToInstructorPage.role_select, 'TC Admin'):
            return False

        time.sleep(1)

        # Select course
        course_name_on_ecard = available_courses.course_name_on_eCard(product_code)
        if not course_name_on_ecard:
            logger.error(f"Course name not found for product code: {product_code}")
            return False

        if not select_by_text(driver, AssignToInstructorPage.course_select, course_name_on_ecard):
            return False

        time.sleep(1)

        # Select training center
        if not select_by_text(driver, AssignToInstructorPage.training_center_select, 'Shell CPR, LLC.'):
            return False

        time.sleep(1)

        # Click assign to dropdown
        if not click_element_by_js(driver, AssignToInstructorPage.instructor_select):
            return False

        time.sleep(1)

        # Select instructor by name
        instructor_name = format_name(name)
        if not click_element_by_js(driver, AssignToInstructorPage.instructor_name_selector(instructor_name)):
            return False

        time.sleep(1)

        # Click move next
        if not click_element_by_js(driver, AssignToInstructorPage.submit_button):
            return False

        time.sleep(1)

        # Input quantity
        if not input_element(driver, AssignToInstructorPage.quantity_input, str(quantity)):
            return False

        time.sleep(1)

        # Click confirm
        if not click_element_by_js(driver, AssignToInstructorPage.continue_button):
            return False

        time.sleep(1)

        # Click complete
        if not click_element_by_js(driver, AHAInventoryPage.finish_button):
            return False

        time.sleep(1)

        # Go to inventory
        if not click_element_by_js(driver, AHAInventoryPage.go_to_inventory_button):
            return False

        logger.info(f"Successfully assigned {quantity} of {product_code} ({'Individual' if available_courses.is_individual_course(product_code) else 'Bundle'}) to instructor {name}")
        return True

    except Exception as e:
        time.sleep(3)
        logger.error(f"Error occurred while assigning to instructor: {e}")
        return False

    logger.error("Failed to assign to instructor")
    return False


def assign_to_training_center(driver, name: str, quantity: str, product_code: str, training_site: str) -> bool:
    """Assign to training center with comprehensive error handling."""
    if not available_courses:
        logger.error("Available courses not initialized")
        return False

    # Check if this is appropriate for training site assignment
    if available_courses.is_individual_course(product_code):
        logger.info(f"Course {product_code} is an individual course - typically assigned to instructors, but proceeding with training site assignment as requested")

    try:
        available_course_selector = f"{AHAInventoryPage.available_course_selector(product_code)}[@role='button']"
        # Click on the course
        if not click_element_by_js(driver, available_course_selector):
            return False

        time.sleep(1)

        # Click 'Assign to Training Site'
        if not click_element_by_js(driver, AHAInventoryPage.assign_to('Training Site')):
            return False

        time.sleep(2)

        # Select training center
        if not select_by_text(driver, AssignToTrainingCenterPage.training_center_select, 'Shell CPR, LLC.'):
            return False

        time.sleep(1)

        # Select training site
        if not select_by_text(driver, AssignToTrainingCenterPage.training_site_select, training_site):
            return False

        time.sleep(1)

        # Select course
        course_name_on_ecard = available_courses.course_name_on_eCard(product_code)
        if not course_name_on_ecard:
            logger.error(f"Course name not found for product code: {product_code}")
            return False

        if not select_by_text(driver, AssignToTrainingCenterPage.course_select, course_name_on_ecard):
            return False

        time.sleep(1)

        # Input quantity
        if not input_element(driver, AssignToTrainingCenterPage.quantity_input, str(quantity)):
            return False

        # Click validate
        if not click_element_by_js(driver, AssignToTrainingCenterPage.submit_button):
            return False

        time.sleep(1)

        # Click complete
        if not click_element_by_js(driver, AHAInventoryPage.finish_button):
            return False

        time.sleep(1)

        # Go to inventory
        if not click_element_by_js(driver, AHAInventoryPage.go_to_inventory_button):
            return False

        if training_site != 'Code Blue CPR Services, LLC':
            return True

        logout_from_aha(driver)
        safe_navigate_to_url(driver, "https://ecards.heart.org/inventory")
        login_to_ecards(driver, username=os.getenv("AHA_NEW_USERNAME"), password=os.getenv("AHA_NEW_PASSWORD"))

        if not click_element_by_js(driver, available_course_selector):
            return False

        # Click 'Assign to Instructor'
        if not click_element_by_js(driver, AHAInventoryPage.assign_to('Instructor')):
            return False

        if not select_by_text(driver, AssignToInstructorPage.role_select, 'TSC'):
            logger.error("Failed to select TS Admin")
            return False

        # Select course
        course_name_on_ecard = available_courses.course_name_on_eCard(product_code)
        if not course_name_on_ecard:
            logger.error(f"Course name not found for product code: {product_code}")
            return False

        if not select_by_text(driver, AssignToInstructorPage.course_select, course_name_on_ecard):
            return False

        # Select training center
        if not select_by_text(driver, AssignToInstructorPage.training_center_select, 'Shell CPR, LLC.'):
            return False

        time.sleep(1)

        # Select training site
        if not select_by_text(driver, AssignToInstructorPage.training_site_select, training_site):
            return False

        time.sleep(1)

        # Click assign to dropdown
        if not click_element_by_js(driver, AssignToInstructorPage.instructor_select):
            return False

        time.sleep(1)

        # Select instructor by name
        instructor_name = format_name(name)
        if not click_element_by_js(driver, AssignToInstructorPage.instructor_name_selector(instructor_name)):
            return False

        time.sleep(1)

        # Click move next
        if not click_element_by_js(driver, AssignToInstructorPage.submit_button):
            return False

        time.sleep(1)

        # Input quantity
        if not input_element(driver, AssignToInstructorPage.quantity_input, str(quantity)):
            return False

        time.sleep(1)

        # Click confirm
        if not click_element_by_js(driver, AssignToInstructorPage.continue_button):
            return False

        time.sleep(1)

        # Click complete
        if not click_element_by_js(driver, AHAInventoryPage.finish_button):
            return False

        time.sleep(1)

        # Go to inventory
        if not click_element_by_js(driver, AHAInventoryPage.go_to_inventory_button):
            return False

        logout_from_aha(driver)
        login_to_ecards(driver, username=os.getenv("ATLAS_USERNAME"), password=os.getenv("ATLAS_PASSWORD"))

        logger.info(f"Successfully assigned {quantity} of {product_code} ({'Individual' if available_courses.is_individual_course(product_code) else 'Bundle'}) to training site {training_site}")
        return True

    except Exception as e:
        time.sleep(3)
        return False


def logout_from_aha(driver):
    try:
        click_element_by_js(driver, (By.XPATH, "//img[@id= 'profileImg']/parent::button"))
        click_element_by_js(driver, (By.ID, "logoutId"))
        time.sleep(1)
        header_username = (By.XPATH, "//span[contains(@class, 'Header_userName')]/ancestor::button")
        ele = check_element_exists(driver, header_username)
        if not ele:
            return
        move_to_element(driver, header_username)
        click_element_by_js(driver, (By.XPATH, "//a[text()= 'Logout']"))
    except Exception as e:
        logger.error(f"Error during logout from AHA: {e}")


def assign_to_admin_instructor(driver, name: str, quantity: str, product_code: str) -> bool:
    """Assign to Admin Instructor - For ACLS/PALS courses."""
    if not available_courses:
        logger.error("Available courses not initialized")
        return False

    logger.info(f"Assigning {quantity} of {product_code} to Admin Instructor for {name}")
    try:
        safe_navigate_to_url(driver, "https://ecards.heart.org/InstructorAssignment")

        time.sleep(2)

        # Step 3: Select TS Admin role
        if not select_by_text(driver, AssignToInstructorPage.role_select, 'TS Admin'):
            logger.error("Failed to select TS Admin")
            return False

        time.sleep(1)

        # Step 4: Select course
        course_name_on_ecard = available_courses.course_name_on_eCard(product_code)
        if not course_name_on_ecard:
            logger.error(f"Course name not found for product code: {product_code}")
            return False

        if not select_by_text(driver, AssignToInstructorPage.course_select, course_name_on_ecard):
            logger.error("Failed to select course for Admin Instructor")
            return False

        time.sleep(1)

        # Step 5: Select Training Center
        if not select_by_text(driver, AssignToInstructorPage.training_center_select, 'CPR Suppliers, LLC'):
            logger.error("Failed to select Training Center")
            return False

        time.sleep(1)

        # Step 6: Select Training Site
        if not select_by_text(driver, AssignToInstructorPage.training_site_select, 'Shell CPR'):
            logger.error("Failed to select Training Site")
            return False

        time.sleep(1)

        # Step 7: Select Instructor
        if not click_element_by_js(driver, AssignToInstructorPage.instructor_select):
            logger.error("Failed to open instructor dropdown")
            return False

        time.sleep(1)

        instructor_name = format_name(name)
        if not click_element_by_js(driver, AssignToInstructorPage.instructor_name_selector(instructor_name)):
            logger.error(f"Failed to select instructor: {name}")
            return False

        time.sleep(1)

        # Step 8: Click Submit button
        if not click_element_by_js(driver, AssignToInstructorPage.submit_button):
            logger.error("Failed to click Submit button")
            return False

        time.sleep(1)

        # Check available quantity
        available_qyt_element = get_element_text(driver, AssignToInstructorPage.available_quantity, default="0")
        available_qyt = int(available_qyt_element) if available_qyt_element.isdigit() else 0

        if available_qyt < int(quantity):
            logger.warning(f"Insufficient quantity for {product_code}. Available: {available_qyt}, Required: {quantity}")

            # Navigate back to inventory without retrying
            try:
                # Try to go back to inventory directly
                if click_element_by_js(driver, (By.XPATH, "//a[text()= 'Go To Inventory']")):
                    logger.info("Successfully returned to inventory due to insufficient quantity")
                else:
                    # Alternative method: try to navigate back via browser back
                    driver.get("https://ecards.heart.org/Inventory")
                    time.sleep(2)
                    logger.info("back to inventory via URL navigation")
            except Exception as nav_error:
                logger.error(f"Error navigating back to inventory: {nav_error}")

            return False  # Return False but don't retry

        # Input quantity
        if not input_element(driver, AssignToInstructorPage.quantity_input, str(quantity)):
            logger.error("Failed to input quantity")
            return False

        time.sleep(1)

        # Click confirm
        if not click_element_by_js(driver, AssignToInstructorPage.continue_button):
            logger.error("Failed to confirm assignment")
            return False

        time.sleep(1)

        # Click complete
        if not click_element_by_js(driver, AHAInventoryPage.finish_button):
            logger.error("Failed to complete assignment")
            return False

        time.sleep(1)

        # Go to inventory
        if not click_element_by_js(driver, AHAInventoryPage.go_to_inventory_button):
            logger.error("Failed to return to inventory")
            return False

        logger.info(f"Successfully assigned {quantity} of {product_code} (ACLS/PALS) to Admin Instructor for {name}")
        return True

    except Exception as e:
        logger.error(f"Admin Instructor assignment failed: {e}")
        return False


def format_name(name: str) -> str:
    """Format a full name with smart title casing (handles Mc, Mac, O', and hyphens)."""

    parts = name.split()
    if len(parts) >= 2 and parts[0][:1].isupper() and parts[-1][:1].isupper():
        return name

    def smart_cap(word: str) -> str:
        # NEW: Handle hyphenated names (e.g., Abdul-Majied, Anne-Marie)
        # We split the word by the hyphen, process each part individually, and rejoin.
        if "-" in word:
            return "-".join(smart_cap(part) for part in word.split("-"))

        # --- Existing Logic Below ---
        w = word.lower().capitalize()

        # Handle O' prefix (e.g., O'Neil, O'Connor)
        if re.match(r"^o'[a-z]", w.lower()):
            return "O'" + w[2:].capitalize()

        # Handle Mc prefix (e.g., McKinney, McDonald)
        if w.lower().startswith("mc") and len(w) > 2:
            return "Mc" + w[2].upper() + w[3:]

        # Handle Mac prefix (e.g., MacArthur, MacGregor)
        if w.lower().startswith("mac") and len(w) > 3:
            return "Mac" + w[3].upper() + w[4:]

        return w

    return " ".join(smart_cap(word) for word in name.split())