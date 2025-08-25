from selenium.webdriver.common.by import By
from Utils.utils import *
import os
from dotenv import load_dotenv
from courses import AvailableCourses
import csv

available_courses = AvailableCourses()
# Load environment variables from .env file
load_dotenv()


def login_to_enrollware_and_navigate_to_tc_product_orders(driver):
    try:
        driver.get("https://enrollware.com/admin")
        time.sleep(5)
        validation_button = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.ID, "loginButton")))
        if validation_button:
            input_element(driver, (By.ID, "username"), os.getenv("ENROLLWARE_USERNAME"))
            input_element(driver, (By.ID, "password"), os.getenv("ENROLLWARE_PASSWORD"))
            click_element_by_js(driver, (By.ID, "rememberMe"))
            click_element_by_js(driver, (By.ID, "loginButton"))
            time.sleep(20)
            print("Logged In Successfully.\nNavigating to TC Product Orders")
            navigate_to_tc_product_orders(driver)
    except:
        print(f"Already Logged In, Navigating to TC Product Orders")
        navigate_to_tc_product_orders(driver)


def navigate_to_tc_product_orders(driver):
    try:
        driver.get("https://www.enrollware.com/admin/tc-product-order-list-tc.aspx")
    except Exception as e:
        print(f"Error navigating to TC Product Orders: {e}")
        pass

def login_to_atlas(driver):
    try:
        sign_in_button = check_element_exists(driver, (By.XPATH, "(//button[text()= 'Sign In | Sign Up'])[1]"))
        if sign_in_button:
            click_element_by_js(driver, (By.XPATH, "(//button[text()= 'Sign In | Sign Up'])[1]"))
            print("Navigating to Atlas Sign In Page")
            time.sleep(2)
            if driver.current_url == "https://atlas.heart.org/dashboard":
                print("Logged In to Atlas")
                return
            try:
                email_entered = check_element_exists(driver, (By.XPATH, f'''//input[@value= '{os.getenv("ATLAS_USERNAME")}']'''))
                if email_entered:
                    input_element(driver, (By.ID, "Password"), os.getenv("ATLAS_PASSWORD"))
                    time.sleep(2)
                    click_element_by_js(driver, (By.ID, "btnSignIn"))
                    print("Signed In Successfully.")
                    return
                else:
                    input_element(driver, (By.ID, "Email"), os.getenv("ATLAS_USERNAME"))
                    time.sleep(2)
                    input_element(driver, (By.ID, "Password"), os.getenv("ATLAS_PASSWORD"))
                    time.sleep(2)
                    click_element_by_js(driver, (By.ID, "RememberMe"))
                    time.sleep(2)
                    click_element_by_js(driver, (By.ID, "btnSignIn"))
            except:
                pass
        else:
            print("Sign In button not found. Skipping login to Atlas.")
            pass
    except Exception as e:
        print(f"Error during Atlas login: {e}")
        pass


def navigate_to_eCard_section(driver):
    try:
        move_to_element(driver, (By.XPATH, "//button[@id= 'Training Center']"))
        click_element_by_js(driver, (By.XPATH, "//a[@title= 'eCards']"))
    except Exception as e:
        print(f"Error navigating to eCard section: {e}")

def get_indexes_to_process(driver):
    valid_indexes = []
    
    # find all rows inside the table
    rows = driver.find_elements(By.XPATH, "//tbody/tr")
    
    for i, row in enumerate(rows, start=1):  # start=1 for 1-based index
        try:
            td2 = row.find_element(By.XPATH, ".//td[2]").text.strip().lower()
        except:
            td2 = ""
        try:
            td4 = row.find_element(By.XPATH, ".//td[4]").text.strip().lower()
        except:
            td4 = ""
        
        # exclusion conditions
        if "redcross" in td2 or "red cross" in td2:
            continue
        if "complete" in td4:
            continue
        
        # if not excluded → keep index
        valid_indexes.append(i)
    return valid_indexes

def create_xpath(title):
    return f"//label[text()= '{title}:']/parent::div/following-sibling::div"

def get_order_data(driver):
    try:
        order_data = []
        training_site = get_element_text(driver, (By.XPATH, create_xpath('Training Site'))).strip()
        name = get_element_text(driver, (By.XPATH, create_xpath('Name/Address')))
        name = name.split('\n')[0].strip() if "\n" in name else name.strip()
        num_of_orders = int(len(driver.find_elements(By.XPATH, f"{create_xpath('Products')}//tr"))) - 1
        quantity_ele = driver.find_elements(By.XPATH, f"{create_xpath('Products')}//td[1]")
        product_code_ele = driver.find_elements(By.XPATH, f"{create_xpath('Products')}//td[2]")
        course_name_ele = driver.find_elements(By.XPATH, f"{create_xpath('Products')}//td[3]")
        for i in range(num_of_orders):
            quantity = quantity_ele[i].text.strip()
            product_code = product_code_ele[i].text.strip()
            course_name = course_name_ele[i].text.strip()
            order_data.append({
                "training_site": training_site,
                "name": name,
                "quantity": quantity,
                "product_code": product_code,
                "course_name": course_name
            })
        return order_data, num_of_orders
    except Exception as e:
        print(f"Error processing row: {e}")
        raise e

def mark_order_as_complete(driver):
    try:
        select_by_text(driver, (By.ID, "mainContent_status"), 'Complete')
        click_element_by_js(driver, (By.ID, "mainContent_statusUpdateBtn"))
        time.sleep(2)
        click_element_by_js(driver, (By.ID, "mainContent_emailBtn"))
        time.sleep(2)
        click_element_by_js(driver, (By.ID, "mainContent_sendButton"))
        time.sleep(2)
        click_element_by_js(driver, (By.ID, "mainContent_backButton"))
    except Exception as e:
        print(f"Error marking order as complete: {e}")


def course_not_available(driver, product_code):
    try:
        print(f"Course {product_code} is not available for eCard generation.")
        go_back(driver)
        click_element_by_js(driver, (By.ID, "mainContent_backButton"))
    except Exception as e:
        print(f"Error handling course not available: {e}")
        pass

def qyt_not_available(driver, product_code, available_qyt_on_ecard, quantity):
    try:
        print(f"Quantity not available for {product_code}. Available: {available_qyt_on_ecard}, Requested: {quantity}")
        go_back(driver)
        click_element_by_js(driver, (By.ID, "mainContent_backButton"))
    except Exception as e:
        print(f"Error handling quantity not available: {e}")
        pass

def go_back(driver):
    try:
        driver.close()
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(2)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    except Exception as e:
        print(f"Error going back: {e}")
        pass

def assign_to_instructor(driver, name, quantity, product_code):
    try:
        time.sleep(2)
        available_course_selector = f"//td[contains(text(), '{product_code}')]/preceding-sibling::td[@role='button']"
        click_element_by_js(driver, (By.XPATH, available_course_selector))
        time.sleep(2)
        click_element_by_js(driver, (By.XPATH, f"//div/a[contains(text(), 'Assign to Instructor')]"))
        time.sleep(2)
        select_by_text(driver, (By.ID, "RoleId"), 'TC Admin')
        time.sleep(2)
        select_by_text(driver, (By.ID, "CourseId"), available_courses.course_name_on_eCard(product_code))
        time.sleep(2)
        select_by_text(driver, (By.ID, "ddlTC"), 'Shell CPR, LLC.')
        time.sleep(2)
        click_element_by_js(driver, (By.XPATH, "//select[@id= 'assignTo']/following-sibling::div/button"))
        time.sleep(2)
        click_element_by_js(driver, (By.XPATH, f"(//label[contains(text(), '{name.title()}')])[1]"))
        time.sleep(2)
        click_element_by_js(driver, (By.ID, "btnMoveNext"))
        time.sleep(2)
        input_element(driver, (By.ID, "qty1"), quantity)
        time.sleep(1)
        click_element_by_js(driver, (By.ID, "btnConfirm"))
        time.sleep(2)
        click_element_by_js(driver, (By.ID, "btnComplete"))
        time.sleep(2)
        click_element_by_js(driver, (By.XPATH, "//a[text()= 'Go To Inventory']"))
    except Exception as e:
        print(f"Error assigning to instructor: {e}")
        pass

def assign_to_training_center(driver, quantity, product_code, training_site):
    try:
        available_course_selector = f"//td[contains(text(), '{product_code}')]/preceding-sibling::td[@role='button']"
        click_element_by_js(driver, (By.XPATH, available_course_selector))
        time.sleep(2)
        click_element_by_js(driver, (By.XPATH, f"//div/a[contains(text(), 'Assign to Training Site')]"))
        time.sleep(2)
        select_by_text(driver, (By.ID, "tcId"), 'Shell CPR, LLC.')
        time.sleep(2)
        select_by_text(driver, (By.ID, "tsList"), training_site)
        time.sleep(2)
        select_by_text(driver, (By.ID, "courseId"), available_courses.course_name_on_eCard(product_code))
        time.sleep(2)
        input_element(driver, (By.ID, "qty"), quantity)
        click_element_by_js(driver, (By.ID, "btnValidate"))
        time.sleep(2)
        click_element_by_js(driver, (By.ID, "btnComplete"))
        time.sleep(2)
        click_element_by_js(driver, (By.XPATH, "//a[text()= 'Go To Inventory']"))
    except Exception as e:
        print(f"Error assigning to training site: {e}")
        pass


def get_training_site_name(code):
    csv_path = os.path.join('Utils', 'training_sites.csv')
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['Code'] == code:
                    return row['Text']
        return None
    except FileNotFoundError:
        print(f"Error: {csv_path} not found")
        return None
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None


def login_to_shop_cpr(driver):
    try:
        driver.get("https://shopcpr.heart.org/"
                   "")
        time.sleep(5)
        sign_in_btn = check_element_exists(driver, (By.XPATH, "//a[contains(@href, 'login')]"))
        if sign_in_btn:
            print("Logging in to ShopCPR.")
            click_element_by_js(driver, (By.XPATH, "//a[contains(@href, 'login')]"))
            time.sleep(2)
            input_element(driver, (By.ID, "Email"), os.getenv("SHOP_CPR_USERNAME"))
            time.sleep(2)
            input_element(driver, (By.ID, "Password"), os.getenv("SHOP_CPR_PASSWORD"))
            time.sleep(2)
            click_element_by_js(driver, (By.ID, "btnSignIn"))
            time.sleep(5)
        else:
            print("Already logged in to ShopCPR.")
            pass
    except Exception as e:
        print(f"Error Logging in to ShopCPR. {e}")
        pass

def checkout_popup_handling(driver):
    try:
        popup = check_element_exists(driver, (By.XPATH, "//div[@id= 'org-form']"))
        if popup:
            click_element_by_js(driver, (By.XPATH, "//button[text()= 'Continue']"))
            time.sleep(2)
    except Exception as e:
        print(f"Error handling checkout popup: {e}")
        pass

def make_purchase_on_shop_cpr(driver, product_code, quantity_to_order, name):
    try:
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        login_to_shop_cpr(driver)
        click_element_by_js(driver, (By.XPATH, "//span[text()= 'Course Cards']/parent::a"))
        time.sleep(1)
        click_element_by_js(driver, (By.XPATH, "//span[text()= 'Heartsaver Bundles']/parent::a"))
        time.sleep(2)
        click_element_by_js(driver, (By.XPATH, "//button[@title= 'Search Product']"))
        time.sleep(1)
        input_element(driver, (By.XPATH, "//input[@id= 'searchtext']"), product_code)
        time.sleep(1)
        click_element_by_js(driver, (By.XPATH, "//button[@id= 'btnsearch']"))
        time.sleep(2)
        input_element(driver, (By.XPATH, "//input[@id= 'qty']"), quantity_to_order)
        time.sleep(1)
        click_element_by_js(driver, (By.XPATH, "//button[@id= 'product-addtocart-button']"))
        time.sleep(2)
        click_element_by_js(driver, (By.XPATH, "//a[@id= 'aha-showcart']"))
        time.sleep(1)
        click_element_by_js(driver, (By.ID, "top-cart-btn-checkout"))
        time.sleep(2)
        checkout_popup_handling(driver)
        time.sleep(2)
        input_element(driver, (By.XPATH, "//input[@id= 'sid']"), os.getenv("SHOP_CPR_SECURITY_ID"))
        time.sleep(1)
        click_element_by_js(driver, (By.ID, "proceed-checkout"))
        time.sleep(2)
        input_element(driver, (By.ID, "po_number"), name)
        time.sleep(1)
        click_element_by_js(driver, (By.XPATH, "//button[text()= 'Proceed to Payment']"))
        time.sleep(2)
        if "orderconfirmation" in driver.current_url:
            print(f"Successfully purchased {quantity_to_order} of {product_code} eCards for {name}.")
        else:
            print(f"Failed to complete purchase for {product_code} eCards for {name}.")
        time.sleep(1)
        driver.close()
        time.sleep(0.5)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(0.5)
        driver.refresh()
    except Exception as e:
        print(f"Error in making purchase on ShopCPR: {e}")
        driver.close()
        go_back(driver)
        pass