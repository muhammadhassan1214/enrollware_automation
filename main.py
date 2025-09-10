from Utils.functions import *
from ui_purchasing_toggle import purchasing_enabled, show_ui
import logging
from typing import List, Dict, Any
import sys
import os
from datetime import datetime
import csv

# Configure logging with simplified output
def setup_logging():
    """Setup simplified logging with necessary information only."""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Create timestamp for log file
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_file = f'logs/python_{timestamp}.log'

    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)  # Changed from DEBUG to INFO

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler with simplified format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler with detailed format
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    return log_file

# Setup logging
log_file = setup_logging()
logger = logging.getLogger(__name__)

# Log startup information
print("=" * 50)
print("ENROLLWARE AUTOMATION STARTING")
print("=" * 50)
logger.info(f"Application started - Log file: {log_file}")

FAILED_ORDERS_CSV = "failed_orders.csv"

def log_failed_order(order: Dict[str, Any], reason: str):
    """Append failed order info to failed_orders.csv."""
    file_exists = os.path.isfile(FAILED_ORDERS_CSV)
    with open(FAILED_ORDERS_CSV, "a", newline='', encoding='utf-8') as csvfile:
        fieldnames = list(order.keys()) + ["failure_reason"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        order_row = dict(order)
        order_row["failure_reason"] = reason
        writer.writerow(order_row)

class OrderProcessor:
    def __init__(self):
        self.available_courses = None
        self.driver = None

    def initialize(self) -> bool:
        """Initialize the order processor with safe exception handling."""
        try:
            logger.info("Initializing automation components...")
            self.available_courses = AvailableCourses()

            self.driver = get_undetected_driver()
            if self.driver:
                logger.info("Chrome driver initialized successfully")
                return True
            else:
                logger.error("Failed to initialize Chrome driver")
                return False
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False

    def cleanup(self):
        """Safely cleanup resources."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Resources cleaned up successfully")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

    def safe_click_back_button(self):
        """Safely click the back button with retry logic."""
        for attempt in range(3):
            try:
                click_element_by_js(self.driver, (By.ID, "mainContent_backButton"))
                return True
            except Exception as e:
                logger.warning(f"Back button click attempt {attempt + 1} failed: {e}")
                time.sleep(1)
        return False

    def safe_navigate_back(self):
        """Safely navigate back with multiple attempts."""
        try:
            go_back(self.driver)
        except Exception as e:
            logger.warning(f"Go back failed, trying alternative: {e}")
            self.safe_click_back_button()

    def should_skip_course(self, course_name: str, product_code: str) -> tuple[bool, str]:
        """Check if course should be skipped and return reason."""
        try:
            if 'red cross' in course_name.lower() or 'redcross' in course_name.lower():
                return True, f"Red Cross course: {course_name}"

            if not self.available_courses.is_course_available(product_code):
                return True, f"Course {product_code} is not available for eCard generation"

            # Log course category for debugging
            course_type = "Individual" if self.available_courses.is_individual_course(product_code) else "Bundle"
            logger.debug(f"Course {product_code} is a {course_type} course")

            return False, ""
        except Exception as e:
            logger.error(f"Error checking course availability: {e}")
            return True, f"Error checking course: {e}"

    def setup_eCards_session(self) -> bool:
        """Setup eCards session in new tab with retry logic (avoids duplicate eCard tabs)."""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                self.driver.execute_script("window.open('');")
                self.driver.switch_to.window(self.driver.window_handles[-1])

                self.driver.get("https://ecards.heart.org/inventory")
                time.sleep(3)

                maintenance_msg = check_element_exists(self.driver, (By.XPATH, "//span[contains(text(), 'Our site will be under maintenance')]"))
                if maintenance_msg:
                    logger.error("eCards site is under maintenance")
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    return False

                login_to_ecards(self.driver)

                # If redirected to log in after click, try once more
                if "login" in self.driver.current_url.lower():
                    login_to_ecards(self.driver)

                return True

            except Exception as e:
                logger.error(f"eCards session setup attempt {attempt + 1} failed: {e}")
                # Cleanup tab if partially opened
                try:
                    if len(self.driver.window_handles) > 1:
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                except Exception:
                    pass
                if attempt < max_attempts - 1:
                    time.sleep(2)

        logger.error("Failed to setup eCards session")
        return False

    def is_acls_pals_course(self, course_name: str) -> bool:
        """Check if course is ACLS or PALS based on course name."""
        if not course_name:
            return False

        course_upper = course_name.upper()
        return 'ACLS' in course_upper or 'PALS' in course_upper

    def process_order_assignment(self, order_data: List[Dict[str, Any]], training_site: str,
                               available_qyt_selector: str) -> bool:
        """Process order assignment with proper exception handling and individual order logic."""
        all_success = True
        for order in order_data:
            product_code = order.get('product_code', '')
            course_name = order.get('course_name', '')
            name = order.get('name', '')
            quantity = order.get('quantity', 0)

            logger.info(f"Processing individual order: {product_code} - {course_name}")

            try:
                # Priority check: ACLS/PALS courses go to Admin Instructor
                if self.is_acls_pals_course(course_name):
                    logger.info(f"ACLS/PALS course {product_code} ({course_name}) assigned to Admin Instructor")
                    if not assign_to_admin_instructor(self.driver, name, str(quantity), product_code):
                        reason = f"Failed to assign ACLS/PALS course {product_code} to Admin Instructor"
                        logger.error(reason)
                        log_failed_order(order, reason)
                        all_success = False
                    continue

                # For non-ACLS/PALS courses, apply individual/bundle logic
                if self.available_courses.is_individual_course(product_code):
                    if training_site.startswith("TS"):
                        logger.info(f"Individual course {product_code} assigned to training site due to TS prefix")
                        if not self.process_single_order(order, available_qyt_selector,
                                                        lambda driver, name, qty, code: assign_to_training_center(driver, qty, code, self.get_training_site_name_for_order(training_site))):
                            reason = f"Failed to assign individual course {product_code} to training site"
                            logger.error(reason)
                            log_failed_order(order, reason)
                            all_success = False
                    else:
                        logger.info(f"Individual course {product_code} assigned to instructor")
                        if not self.process_single_order(order, available_qyt_selector, assign_to_instructor):
                            reason = f"Failed to assign individual course {product_code} to instructor"
                            logger.error(reason)
                            log_failed_order(order, reason)
                            all_success = False
                else:
                    # Bundle courses: prefer training site assignment
                    logger.info(f"Bundle course {product_code} assigned to training site")
                    if not self.process_single_order(order, available_qyt_selector,
                                                    lambda driver, name, qty, code: assign_to_training_center(driver, qty, code, self.get_training_site_name_for_order(training_site))):
                        reason = f"Failed to assign bundle course {product_code} to training site"
                        logger.error(reason)
                        log_failed_order(order, reason)
                        all_success = False
            except Exception as e:
                reason = f"Exception during order assignment: {e}"
                logger.error(reason)
                log_failed_order(order, reason)
                all_success = False

        return all_success

    def get_training_site_name_for_order(self, training_site: str) -> str:
        """Get training site name for order assignment."""
        code = training_site.split(' ')[0].strip() if ' ' in training_site else training_site.strip()
        training_site_name = get_training_site_name(code)
        return training_site_name if training_site_name else "Unknown Training Site"

    def process_admin_instructor_assignment(self, order_data: List[Dict[str, Any]]) -> bool:
        """Process Admin Instructor assignment for ACLS/PALS courses with exception handling."""
        try:
            # This method is now only called for ACLS/PALS bypass scenario
            # Individual order processing is handled in process_order_assignment
            for order in order_data:
                name = order.get('name', '')
                product_code = order.get('product_code', '')
                quantity = order.get('quantity', 0)

                # For ACLS/PALS courses, bypass quantity checks and proceed directly
                if not assign_to_admin_instructor(self.driver, name, str(quantity), product_code):
                    return False
            return True
        except Exception as e:
            logger.error(f"Error in Admin Instructor assignment: {e}")
            return False

    def process_instructor_assignment(self, order_data: List[Dict[str, Any]], available_qyt_selector: str) -> bool:
        """Process instructor assignment with exception handling."""
        try:
            # This method is now only used for non-mixed order scenarios
            for order in order_data:
                if not self.process_single_order(order, available_qyt_selector, assign_to_instructor):
                    return False
            return True
        except Exception as e:
            logger.error(f"Error in instructor assignment: {e}")
            return False

    def process_training_site_assignment(self, order_data: List[Dict[str, Any]], training_site: str,
                                       available_qyt_selector: str) -> bool:
        """Process training site assignment with exception handling."""
        try:
            # This method is now only used for non-mixed order scenarios
            code = training_site.split(' ')[0].strip() if ' ' in training_site else training_site.strip()
            training_site_name = get_training_site_name(code)

            for order in order_data:
                if not self.process_single_order(order, available_qyt_selector,
                                                lambda driver, name, qty, code: assign_to_training_center(driver, qty, code, training_site_name)):
                    return False
            return True
        except Exception as e:
            logger.error(f"Error in training site assignment: {e}")
            return False

    def process_single_order(self, order: Dict[str, Any], available_qyt_selector: str,
                           assignment_func) -> bool:
        """Process a single order with exception handling."""
        try:
            name = order.get('name', '')
            product_code = order.get('product_code', '')
            quantity = order.get('quantity', 0)

            # Get available quantity
            xpath = available_qyt_selector.format(product_code)
            available_qyt_text = get_element_text(self.driver, (By.XPATH, xpath))
            available_qyt = int(available_qyt_text) if available_qyt_text.isdigit() else 0
            quantity_int = int(quantity) if str(quantity).isdigit() else 0

            # Purchase additional if needed
            if available_qyt < quantity_int:
                quantity_to_order = quantity_int - available_qyt
                if purchasing_enabled():
                    logger.info(f"Purchasing {quantity_to_order} additional eCards for {product_code}")
                    purchase_success = make_purchase_on_shop_cpr(self.driver, product_code, quantity_to_order, name)
                    if not purchase_success:
                        reason = f"Failed to purchase {quantity_to_order} eCards for {product_code}"
                        logger.error(reason)
                        log_failed_order(order, reason)
                        return False

                    # Refresh eCards inventory page after successful purchase
                    logger.info("Refreshing eCards inventory after purchase...")
                    self.driver.refresh()
                    time.sleep(5)  # Wait for inventory to update
                else:
                    logger.info(f"Purchasing is OFF. Please purchase {quantity_to_order} of {product_code} manually for order {name}.")
                    # Skip purchase, continue with next order
                    return True

            # Assign the order
            if not assignment_func(self.driver, name, quantity, product_code):
                reason = f"Assignment function failed for {product_code}"
                logger.error(reason)
                log_failed_order(order, reason)
                return False
            return True

        except Exception as e:
            reason = f"Error processing single order: {e}"
            logger.error(reason)
            log_failed_order(order, reason)
            return False

    def process_single_row(self, index: int) -> bool:
        """Process a single row with comprehensive exception handling."""
        try:
            logger.info(f"Processing row {index}...")
            click_element_by_js(self.driver, (By.XPATH, f"//tbody/tr[{index}]/td[7]/a"))

            # Get order data
            order_data, num_of_orders = get_order_data(self.driver)
            if not order_data:
                logger.warning(f"No order data found for row {index}")
                self.safe_click_back_button()
                return False

            # Log all orders in this row
            logger.info(f"Found {len(order_data)} orders in row {index}:")
            for i, order in enumerate(order_data, 1):
                course_name = order.get('course_name', '')
                product_code = order.get('product_code', '')
                quantity = order.get('quantity', 0)
                logger.info(f"  {i}. {quantity} {product_code} {course_name}")

            first_order = order_data[0]
            name = first_order.get('name', '')
            training_site = first_order.get('training_site', '')

            logger.info(f"Processing for: {name} - Training Site: {training_site}")

            # Check if any order contains ACLS/PALS
            has_acls_pals = any(self.is_acls_pals_course(order.get('course_name', '')) for order in order_data)
            if has_acls_pals:
                acls_pals_courses = [order.get('course_name', '') for order in order_data if self.is_acls_pals_course(order.get('course_name', ''))]
                logger.info(f"Detected ACLS/PALS courses in order: {acls_pals_courses}")

            # Check if any course should be skipped
            for order in order_data:
                course_name = order.get('course_name', '')
                product_code = order.get('product_code', '')
                should_skip, skip_reason = self.should_skip_course(course_name, product_code)
                if should_skip:
                    logger.info(f"Skipping entire order due to: {skip_reason}")
                    self.safe_click_back_button()
                    return True  # Not an error, just skipped

            # Setup eCards session
            if not self.setup_eCards_session():
                logger.error(f"Failed to setup eCards session for row {index}")
                self.safe_click_back_button()
                return False

            # Check if all orders are ACLS/PALS (bypass inventory checks completely)
            all_acls_pals = all(self.is_acls_pals_course(order.get('course_name', '')) for order in order_data)

            if all_acls_pals:
                logger.info(f"All courses are ACLS/PALS - bypassing inventory checks completely")

                # Process all ACLS/PALS assignments directly without inventory checks
                if self.process_admin_instructor_assignment(order_data):
                    # Complete the order
                    self.safe_navigate_back()
                    mark_order_as_complete(self.driver)
                    logger.info(f"✓ Successfully completed all ACLS/PALS row {index}")
                    return True
                else:
                    logger.error(f"✗ Failed to process all ACLS/PALS assignments for row {index} - no retry")
                    self.safe_navigate_back()
                    self.safe_click_back_button()
                    return False

            # For mixed orders or non-ACLS/PALS courses, proceed with inventory checks for non-ACLS/PALS items
            non_acls_pals_orders = [order for order in order_data if not self.is_acls_pals_course(order.get('course_name', ''))]

            if non_acls_pals_orders:
                logger.info(f"Checking inventory for {len(non_acls_pals_orders)} non-ACLS/PALS courses")

                # Check inventory availability for non-ACLS/PALS courses
                for order in non_acls_pals_orders:
                    product_code = order.get('product_code', '')
                    quantity_needed = int(order.get('quantity', 1))

                    common_selector = f"//td[contains(text(), '{product_code}')]/preceding-sibling::td"
                    available_course_selector = f"{common_selector}[@role='button']"

                    available_course = check_element_exists(self.driver, (By.XPATH, available_course_selector))
                    if not available_course:
                        logger.warning(f"Course {product_code} not available in eCards inventory, purchasing...")

                        # Check if purchasing is enabled before attempting purchase
                        if purchasing_enabled():
                            # Purchase the exact quantity needed (no retry logic)
                            purchase_success = make_purchase_on_shop_cpr(self.driver, product_code, quantity_needed, name)
                            if not purchase_success:
                                logger.error(f"Failed to purchase {quantity_needed} eCards for {product_code}")
                                self.safe_navigate_back()
                                self.safe_click_back_button()
                                return False

                            # Refresh eCards inventory page after purchase
                            logger.info("Refreshing eCards inventory after purchase...")
                            self.driver.refresh()
                            time.sleep(5)  # Wait for inventory to update

                            # Check again if course is now available
                            available_course = check_element_exists(self.driver, (By.XPATH, available_course_selector))
                            if not available_course:
                                logger.error(f"Course {product_code} still not available after purchase")
                                self.safe_navigate_back()
                                self.safe_click_back_button()
                                return False
                        else:
                            logger.info(f"Purchasing is OFF. Course {product_code} is not available in inventory and cannot be purchased automatically. Skipping order for {name}.")
                            reason = f"Course {product_code} not available in inventory and purchasing is disabled"
                            log_failed_order(order, reason)
                            self.safe_navigate_back()
                            self.safe_click_back_button()
                            return False

            # Process mixed order assignment (each order individually)
            common_selector_base = "//td[contains(text(), '{}')]/preceding-sibling::td[1]"

            assignment_success = False
            for assignment_attempt in range(2):  # Retry assignment once if it fails
                if self.process_order_assignment(order_data, training_site, common_selector_base):
                    assignment_success = True
                    break
                else:
                    logger.warning(f"Assignment attempt {assignment_attempt + 1} failed for row {index}")
                    if assignment_attempt < 1:  # If not last attempt
                        time.sleep(3)

            if not assignment_success:
                logger.error(f"Failed to process order assignment for row {index} after all attempts")
                self.safe_navigate_back()
                self.safe_click_back_button()
                return False

            # Complete the order
            self.safe_navigate_back()
            mark_order_as_complete(self.driver)

            logger.info(f"✓ Successfully completed row {index} with {len(order_data)} orders")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to process row {index}: {e}")
            # Attempt recovery
            try:
                self.safe_navigate_back()
                self.safe_click_back_button()
            except Exception as recovery_error:
                logger.error(f"Recovery failed for row {index}: {recovery_error}")
            return False

    def process_single_redcross_order(self, index: int) -> bool:
        """Process a single Red Cross order with exception handling."""
        try:
            tc_product_orders_page = "https://www.enrollware.com/admin/tc-product-order-list-tc.aspx"
            if self.driver.current_url != tc_product_orders_page:
                safe_navigate_to_url(self.driver, tc_product_orders_page)
                time.sleep(2)
            logger.info(f"Processing Red Cross order at index {index}...")
            click_element_by_js(self.driver, (By.XPATH, f"//tbody/tr[{index}]/td[7]/a"))
            time.sleep(1)
            roaster_element = check_element_exists(self.driver, (By.XPATH, "//a[text()= 'view roster']"))
            if not roaster_element:
                logger.error(f"No 'view roster' link found for Red Cross order at index {index}")
                self.safe_click_back_button()
                return False
            click_element_by_js(self.driver, (By.XPATH, "//a[text()= 'view roster']"))
            time.sleep(1)
            click_element_by_js(self.driver, (By.ID, "mainContent_cardPrint"))
            time.sleep(1)
            click_element_by_js(self.driver, (By.ID, "mainContent_arcSubmitBtn"))
            time.sleep(0.5)
            wait_while_element_is_displaying(self.driver, By.ID, "arcPleaseWaitRow", timeout=15)
            time.sleep(1)
            error_element = check_element_exists(self.driver, (By.XPATH, "//div[contains(@class, 'statusbarerror')]"))
            if error_element:
                logger.error(f"Error: {index} cannot be processed.")
                safe_navigate_to_url(self.driver, tc_product_orders_page)
                return False
            safe_navigate_to_url(self.driver, tc_product_orders_page)
            click_element_by_js(self.driver, (By.XPATH, f"//tbody/tr[{index}]/td[7]/a"))
            time.sleep(1)
            mark_order_as_complete(self.driver)
            logger.info(f"Successfully processed Red Cross order at index {index}")
            return True
        except Exception as e:
            logger.error(f"Error processing Red Cross order at index {index}: {e}")
            return False


def main():
    logger.info("Starting automation process...")

    # Show the purchasing toggle UI before automation starts
    show_ui()

    processor = OrderProcessor()
    if not processor.initialize():
        logger.error("Failed to initialize order processor")
        return

    try:
        # Login and navigate
        logger.info("Logging into Enrollware...")
        if not login_to_enrollware_and_navigate_to_tc_product_orders(processor.driver):
            logger.error("Failed to login or navigate to TC Product Orders")
            return

        logger.info("Scanning for orders to process...")
        rows_to_process = get_indexes_to_process(processor.driver, "non-redcross")
        redcross_rows = get_indexes_to_process(processor.driver, "redcross")

        if not rows_to_process and not redcross_rows:
            logger.info("No orders found to process")
            return

        logger.info(f"Found {len(rows_to_process)} orders to process")
        aha_successful_rows, aha_failed_rows = 0, 0
        redcross_successful_rows, redcross_failed_rows = 0, 0

        for i, index in enumerate(rows_to_process, 1):
            try:
                logger.info(f"[{i}/{len(rows_to_process)}] Processing order {index}")
                if processor.process_single_row(index):
                    aha_successful_rows += 1
                else:
                    aha_failed_rows += 1
            except Exception as e:
                logger.error(f"Unexpected error processing row {index}: {e}")
                aha_failed_rows += 1
                continue

        # Process Red Cross orders
        logger.info("Processing Red Cross orders...")
        if redcross_rows:
            logger.info(f"Found {len(redcross_rows)} Red Cross orders to process")
            for i, index in enumerate(redcross_rows, 1):
                try:
                    logger.info(f"[{i}/{len(redcross_rows)}] Processing Red Cross order {index}")
                    if processor.process_single_redcross_order(index):
                        redcross_successful_rows += 1
                    else:
                        redcross_failed_rows += 1
                except Exception as e:
                    logger.error(f"Unexpected error processing Red Cross row {index}: {e}")
                    redcross_failed_rows += 1
                    continue
        else:
            logger.info("No Red Cross orders found to process")

        print(f"\n{'='*50}")
        print(f"PROCESSING SUMMARY")
        print(f"{'='*50}")
        print(f"AHA orders processed: {len(rows_to_process)}")
        print(f"Successful: {aha_successful_rows}")
        print(f"Failed: {aha_failed_rows}")
        print(f"{'-'*50}")
        print(f"Red Cross orders processed: {len(redcross_rows)}")
        print(f"Successful: {redcross_successful_rows}")
        print(f"Failed: {redcross_failed_rows}")
        print(f"{'='*50}")

    except Exception as e:
        logger.error(f"Critical error in main process: {e}")
    finally:
        processor.cleanup()


SCHEDULE_INTERVAL_SECONDS = 15 * 60  # 15 minutes

def run_every_15_minutes():
    logger.info("Starting scheduled automation (runs every 15 minutes)")
    run_count = 0

    while True:
        run_count += 1
        start = time.time()
        print(f"\n{'='*50}")
        print(f"SCHEDULED RUN #{run_count}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")

        try:
            main()  # Existing processing logic
        except Exception as e:
            logger.error(f"Unhandled error in scheduled run #{run_count}: {e}")

        elapsed = time.time() - start
        remaining = SCHEDULE_INTERVAL_SECONDS - elapsed

        if remaining > 0:
            next_run_time = datetime.fromtimestamp(time.time() + remaining).strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"Run #{run_count} completed in {elapsed:.1f}s")
            logger.info(f"Next run scheduled for: {next_run_time}")
            logger.info(f"Waiting {remaining/60:.1f} minutes...")
            time.sleep(remaining)
        else:
            logger.info(f"Run #{run_count} took {elapsed:.1f}s (>= 15 minutes). Starting next run immediately.")


if __name__ == "__main__":
    try:
        run_every_15_minutes()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user (Ctrl+C)")
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error in main application: {e}")
    finally:
        print("Application shutting down...")
        logger.info("Application shutdown complete")
