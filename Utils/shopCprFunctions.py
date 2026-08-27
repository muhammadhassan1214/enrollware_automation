import os
import time
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from Utils.pageSelectors import AHALoginPage, ShopCPRPage
from Utils.functions import validate_environment_variables, get_training_site_name, available_courses, logger
from Utils.utils import (
    input_element, get_element_text,
    click_element_by_js, safe_navigate_to_url,
    check_element_exists,
)

load_dotenv()

def login_to_shop_cpr(driver, max_retries: int = 3) -> bool:
    """Login to ShopCPR with comprehensive error handling."""
    if not validate_environment_variables():
        return False

    for attempt in range(max_retries):
        shop_cpr_url = "https://shopcpr.heart.org/"
        try:
            # if not click_element_by_js(driver, (By.XPATH, f"(//a[@href= '{shop_cpr_url}'])[1]")):
            #     logger.error(f"Login to ShopCPR failed for attempt {attempt}")
            #     continue

            if not safe_navigate_to_url(driver, shop_cpr_url):
                logger.error(f"Navigation to ShopCPR failed for attempt {attempt}")
                continue

            time.sleep(5)

            # Check if already logged in
            sign_in_btn = check_element_exists(driver, ShopCPRPage.sign_in_link, timeout=5)

            if sign_in_btn:
                logger.info("Logging into ShopCPR")

                if not click_element_by_js(driver, ShopCPRPage.sign_in_link):
                    logger.error("Failed to click sign-in link")
                    continue

                time.sleep(3)

                if driver.current_url == shop_cpr_url:
                    logger.info(f"Login to ShopCPR succeeded")
                    return True

                # Input credentials
                if not input_element(driver, AHALoginPage.username_input, os.getenv("SHOP_CPR_USERNAME")):
                    logger.error("Failed to input ShopCPR email")
                    continue

                time.sleep(1)

                if not input_element(driver, AHALoginPage.password_input, os.getenv("SHOP_CPR_PASSWORD")):
                    logger.error("Failed to input ShopCPR password")
                    continue

                time.sleep(1)

                if not click_element_by_js(driver, ShopCPRPage.sign_in_button):
                    logger.error("Failed to click ShopCPR sign-in button")
                    continue

                time.sleep(3)

                # Verify login success
                if shop_cpr_url == driver.current_url.lower() or not check_element_exists(driver, ShopCPRPage.sign_in_link, timeout=3):
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
        popup = check_element_exists(driver, ShopCPRPage.popup_form, timeout=5)
        if popup:
            logger.info("Handling checkout popup")
            if click_element_by_js(driver, ShopCPRPage.popup_form_continue_button):
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
            cart_count = get_element_text(driver, ShopCPRPage.cart_count, timeout=3)
            cart_count = cart_count.replace("(", "").replace(")", "").strip() if "(" in cart_count else cart_count.strip()
            logger.info(f"Cart: {cart_count}")
            if int(cart_count) == 0:
                logger.info("Cart is already empty")
                return True

            # Navigate to cart
            if not click_element_by_js(driver, ShopCPRPage.show_cart_button):
                logger.error("Failed to click show cart")
                continue

            time.sleep(2)

            # Click delete buttons
            delete_buttons = driver.find_elements(By.XPATH, "//a[contains(@id, 'delete-item')]")
            for btn in delete_buttons:
                try:
                    btn.click()
                    time.sleep(1)
                    click_element_by_js(driver, ShopCPRPage.delete_item_button)
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Failed to click delete button: {e}")
                    continue

            time.sleep(2)

            # Verify cart is empty
            empty_cart_msg = check_element_exists(driver, ShopCPRPage.empty_cart_message, timeout=5)
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

def make_purchase_on_shop_cpr(driver, product_code: str, quantity_to_order: int, name: str) -> bool:
    """Make purchase on ShopCPR without retry logic. If purchasing fails, move onto the next one."""
    if not validate_environment_variables():
        return False

    is_individual = available_courses.is_individual_course(product_code) if available_courses else False

    try:
        # Login to ShopCPR
        if not login_to_shop_cpr(driver):
            logger.error("Failed to login to ShopCPR for purchase")
            return False

        # Clear cart to ensure no previous items are present
        if not clear_cart_on_shop_cpr(driver):
            logger.error("Failed to clear cart before purchase")
            return False

        # Navigate to Course Cards
        if not click_element_by_js(driver, ShopCPRPage.course_cards_link):
            logger.error("Failed to click Course Cards")
            return False

        time.sleep(1)

        # Navigate to Heartsaver Bundles
        if not click_element_by_js(driver, ShopCPRPage.heart_saver_bundles_link):
            logger.error("Failed to click Heartsaver Bundles")
            return False

        time.sleep(1)

        # check if the results are displaying if not then clear the site cookies and refresh the page
        if not check_element_exists(driver, ShopCPRPage.products_elements, timeout=5):
            driver.delete_all_cookies()
            driver.refresh()
            time.sleep(5)
            if not check_element_exists(driver, ShopCPRPage.products_elements, timeout=5):
                logger.error("Failed to load Course Cards page after clearing cookies")
                return False

        # Click search button
        if not click_element_by_js(driver, ShopCPRPage.search_product_button):
            logger.error("Failed to click search button")
            return False

        time.sleep(1)

        # Search for product
        if not input_element(driver, ShopCPRPage.search_input, product_code):
            logger.error("Failed to input product code for search")
            return False

        time.sleep(1)

        if not click_element_by_js(driver, ShopCPRPage.search_button):
            logger.error("Failed to click search button")
            return False

        time.sleep(2)

        if not is_individual:
            if not click_element_by_js(driver, ShopCPRPage.view_details_button):
                logger.error("Failed to click View Details for bundle")
                return False

            time.sleep(2)

            if not click_element_by_js(driver, ShopCPRPage.add_to_cart_button):
                logger.error("Failed to click Add to Cart for bundle")
                return False


        time.sleep(1)

        if not click_element_by_js(driver, ShopCPRPage.cart_quick_view):
            logger.error("Failed to add to cart")
            return False

        # Input quantity
        if not input_element(driver, ShopCPRPage.quantity_input, str(quantity_to_order)):
            logger.error("Failed to input quantity")
            return False

        # Add to cart
        if not click_element_by_js(driver, ShopCPRPage.add_to_cart_button_2):
            logger.error("Failed to add to cart")
            return False

        # wait for cart to update
        time.sleep(5)

        # Show cart
        if not check_element_exists(driver, ShopCPRPage.cart_wrapper, timeout=5):
            if not click_element_by_js(driver, ShopCPRPage.show_cart_button_2):
                logger.error("Failed to show cart")
                return False

        time.sleep(2)

        # Checkout
        if not click_element_by_js(driver, ShopCPRPage.checkout_button):
            logger.error("Failed to click checkout")
            return False

        time.sleep(1)

        # Handle popup
        checkout_popup_handling(driver)
        time.sleep(1)

        # check if the item can't be buyed
        if check_element_exists(driver, ShopCPRPage.attention_message, timeout=5):
            logger.error(f"Product {product_code} is not available for purchase")
            return False

        # Input security ID
        if not input_element(driver, ShopCPRPage.security_id_input, os.getenv("SHOP_CPR_SECURITY_ID")):
            logger.error("Failed to input security ID")
            return False

        time.sleep(1)

        # Proceed to checkout
        if not click_element_by_js(driver, ShopCPRPage.proceed_checkout):
            logger.error("Failed to proceed to checkout")
            return False

        time.sleep(2)

        if not is_individual: # If the order is a bundle
            if not click_element_by_js(driver, ShopCPRPage.tax_status):
                logger.error("Failed to click purchase code")
                return False

            time.sleep(1)
            training_site_name = get_training_site_name(product_code)
            is_training_site_availabel = check_element_exists(driver, ShopCPRPage.training_site_select(training_site_name))

            if is_training_site_availabel:
                if not click_element_by_js(driver, ShopCPRPage.training_site_select(training_site_name)):
                    logger.error("Failed to select training site")
                    return False
            else:
                if not click_element_by_js(driver, ShopCPRPage.training_site_select('3SLHD-619865-Shell CPR')):
                    logger.error("Failed to select purchase code")
                    return False

            time.sleep(1)

            if not click_element_by_js(driver, ShopCPRPage.continue_purchase):
                logger.error("Failed to apply purchase code")
                return False

            time.sleep(1)

        # Input PO number
        if not input_element(driver, ShopCPRPage.po_number_input, name):
            logger.error("Failed to input PO number")
            return False

        time.sleep(1)

        # Proceed to payment
        if not click_element_by_js(driver, ShopCPRPage.proceed_to_payment):
            logger.error("Failed to proceed to payment")
            return False

        time.sleep(5)

        # Check order confirmation
        if "orderconfirmation" in driver.current_url:
            logger.info(f"Successfully purchased {quantity_to_order} of {product_code} eCards for {name}")
            safe_navigate_to_url(driver, "https://ecards.heart.org/inventory")
            return True
        else:
            logger.error(f"Purchase failed - not on confirmation page. Current URL: {driver.current_url}")
            return False

    except Exception as e:
        logger.error(f"Purchase failed for {product_code}: {e}")
        return False