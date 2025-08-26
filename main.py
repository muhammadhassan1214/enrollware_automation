from Utils.functions import *
import logging
from typing import List, Dict, Any
import sys
import os
from datetime import datetime

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

            return False, ""
        except Exception as e:
            logger.error(f"Error checking course availability: {e}")
            return True, f"Error checking course: {e}"

    def setup_atlas_session(self) -> bool:
        """Setup Atlas session in new tab with retry logic."""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Open new tab
                self.driver.execute_script("window.open('');")
                self.driver.switch_to.window(self.driver.window_handles[-1])

                # Login to Atlas
                self.driver.get("https://atlas.heart.org/dashboard")
                time.sleep(5)
                login_to_atlas(self.driver)
                navigate_to_eCard_section(self.driver)
                time.sleep(2)
                self.driver.switch_to.window(self.driver.window_handles[-1])
                # Check if additional sign-in is needed
                if "login" in self.driver.current_url.lower():
                    login_to_atlas(self.driver)
                    navigate_to_eCard_section(self.driver)
                time.sleep(2)
                return True

            except Exception as e:
                if attempt < max_attempts - 1:
                    time.sleep(2)
                else:
                    logger.error("Failed to setup Atlas session")
                    return False
        return False

    def process_order_assignment(self, order_data: List[Dict[str, Any]], training_site: str,
                               available_qyt_selector: str) -> bool:
        """Process order assignment with proper exception handling."""
        try:
            assignment_site = "Assign to Training Site" if training_site.startswith("TS") else "Assign to Instructor"

            if assignment_site == "Assign to Instructor":
                return self.process_instructor_assignment(order_data, available_qyt_selector)
            elif assignment_site == "Assign to Training Site":
                return self.process_training_site_assignment(order_data, training_site, available_qyt_selector)
            else:
                logger.warning("Unknown assignment site. Skipping this order.")
                return False

        except Exception as e:
            logger.error(f"Error in order assignment: {e}")
            return False

    def process_instructor_assignment(self, order_data: List[Dict[str, Any]], available_qyt_selector: str) -> bool:
        """Process instructor assignment with exception handling."""
        try:
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
            available_qyt_text = get_element_text(self.driver, (By.XPATH, available_qyt_selector))
            available_qyt = int(available_qyt_text) if available_qyt_text.isdigit() else 0
            quantity_int = int(quantity) if str(quantity).isdigit() else 0

            # Purchase additional if needed
            if available_qyt < quantity_int:
                quantity_to_order = quantity_int - available_qyt
                logger.info(f"Purchasing {quantity_to_order} additional eCards for {product_code}")
                make_purchase_on_shop_cpr(self.driver, product_code, quantity_to_order, name)

            # Assign the order
            assignment_func(self.driver, name, quantity, product_code)
            return True

        except Exception as e:
            logger.error(f"Error processing single order: {e}")
            return False

    def process_single_row(self, index: int) -> bool:
        """Process a single row with comprehensive exception handling."""
        try:
            logger.info(f"Processing row {index}...")
            time.sleep(2)
            click_element_by_js(self.driver, (By.XPATH, f"//tbody/tr[{index}]/td[7]/a"))

            # Get order data
            order_data, num_of_orders = get_order_data(self.driver)
            if not order_data:
                logger.warning(f"No order data found for row {index}")
                self.safe_click_back_button()
                return False

            first_order = order_data[0]
            course_name = first_order.get('course_name', '')
            product_code = first_order.get('product_code', '')
            name = first_order.get('name', '')
            training_site = first_order.get('training_site', '')

            logger.info(f"Processing: {name} - {product_code} ({course_name})")

            # Check if course should be skipped
            should_skip, skip_reason = self.should_skip_course(course_name, product_code)
            if should_skip:
                logger.info(f"Skipped: {skip_reason}")
                self.safe_click_back_button()
                return True  # Not an error, just skipped

            # Setup Atlas session
            if not self.setup_atlas_session():
                logger.error(f"Failed to setup Atlas session for row {index}")
                self.safe_click_back_button()
                return False

            # Check course availability
            available_course_selector = f"//td[contains(text(), '{product_code}')]/preceding-sibling::td[@role='button']"
            available_qyt_selector = f"//td[contains(text(), '{product_code}')]/preceding-sibling::td[1]"

            available_course = check_element_exists(self.driver, (By.XPATH, available_course_selector))
            if not available_course:
                logger.warning(f"Course {product_code} not available for eCard generation")
                course_not_available(self.driver, product_code)
                return False

            # Process order assignment
            if not self.process_order_assignment(order_data, training_site, available_qyt_selector):
                logger.error(f"Failed to process order assignment for row {index}")
                self.safe_navigate_back()
                self.safe_click_back_button()
                return False

            # Complete the order
            self.safe_navigate_back()
            mark_order_as_complete(self.driver)

            logger.info(f"✓ Successfully completed row {index}")
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


def main():
    logger.info("Starting automation process...")
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
        rows_to_process = get_indexes_to_process(processor.driver)

        if not rows_to_process:
            logger.info("No orders found to process")
            return

        logger.info(f"Found {len(rows_to_process)} orders to process")
        successful_rows = 0
        failed_rows = 0

        for i, index in enumerate(rows_to_process, 1):
            try:
                logger.info(f"[{i}/{len(rows_to_process)}] Processing order {index}")
                if processor.process_single_row(index):
                    successful_rows += 1
                else:
                    failed_rows += 1
            except Exception as e:
                logger.error(f"Unexpected error processing row {index}: {e}")
                failed_rows += 1
                continue

        print(f"\n{'='*50}")
        print(f"PROCESSING SUMMARY")
        print(f"{'='*50}")
        print(f"Total orders processed: {len(rows_to_process)}")
        print(f"Successful: {successful_rows}")
        print(f"Failed: {failed_rows}")
        print(f"{'='*50}")

    except Exception as e:
        logger.error(f"Critical error in main process: {e}")
    finally:
        processor.cleanup()


SCHEDULE_INTERVAL_SECONDS = 30 * 60  # 30 minutes

def run_every_30_minutes():
    logger.info("Starting scheduled automation (runs every 30 minutes)")
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
            logger.info(f"Run #{run_count} took {elapsed:.1f}s (>= 30 minutes). Starting next run immediately.")


if __name__ == "__main__":
    try:
        run_every_30_minutes()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user (Ctrl+C)")
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error in main application: {e}")
    finally:
        print("Application shutting down...")
        logger.info("Application shutdown complete")
