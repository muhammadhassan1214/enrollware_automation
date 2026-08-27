import re
import os
import csv
import time
import logging
from typing import Optional

from dotenv import load_dotenv
from courses import AvailableCourses
from selenium.webdriver.common.by import By
from Utils.utils import (
    input_element, select_by_text,
    move_to_element, get_element_text,
    click_element_by_js, safe_navigate_to_url,
    check_element_exists,
)


# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables and validate
load_dotenv()

# Validate required environment variables
REQUIRED_ENV_VARS = [
    "ENROLLWARE_USERNAME", "ENROLLWARE_PASSWORD",
    "ATLAS_USERNAME", "ATLAS_PASSWORD", "DISCORD_WEBHOOK_URL",
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


def get_training_site_name(code: str) -> Optional[str]:
    """Get training site name from CSV with comprehensive error handling."""
    if not code:
        logger.warning("Empty code provided for training site lookup")
        return None

    csv_path = os.path.join('data', 'training_sites.csv')

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


def add_error_log(driver, error_txt: str):
    """Add error log to error_logs.txt with timestamp."""
    try:
        comment_already_exists = check_element_exists(driver,
                                                      (By.XPATH, f'''//td[contains(text(), "{error_txt}")]'''))
        if not comment_already_exists:
            input_element(driver, (By.ID, "mainContent_addEntryTxt"), error_txt)
            click_element_by_js(driver, (By.ID, "mainContent_entrySubBtn"))
    except Exception as e:
        logger.error(f"Failed to write to error log: {e}")


def generate_stock_summary(order_data_list):
    # Return None if the list is empty so no email is generated
    if not order_data_list:
        return None

    sku_totals = {}
    for item in order_data_list:
        sku = item["sku"]
        qty = int(item["qty"])

        if sku in sku_totals:
            sku_totals[sku] += qty
        else:
            sku_totals[sku] = qty

    html_message = """
    <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2c3e50; border-bottom: 2px solid #2D8CFF; padding-bottom: 5px;">
            You need to purchase the following e-cards
        </h2>

        <table style="width: 100%; border-collapse: collapse; margin-top: 15px; text-align: left;">
            <thead>
                <tr style="background-color: #f2f2f2;">
                    <th style="padding: 10px; border-bottom: 2px solid #ddd;">SKU / e-Card Type</th>
                    <th style="padding: 10px; border-bottom: 2px solid #ddd;">Quantity Required</th>
                </tr>
            </thead>
            <tbody>
    """

    for sku, total_qty in sorted(sku_totals.items()):
        html_message += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{sku}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>{total_qty}</strong></td>
                </tr>
        """

    html_message += """
            </tbody>
        </table>
    </div>
    """

    return html_message