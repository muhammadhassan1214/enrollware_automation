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
            time.sleep(10)
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
    driver.get("https://atlas.heart.org/dashboard")
    time.sleep(5)
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
        training_site = get_element_text(driver, (By.XPATH, create_xpath('Training Site'))).strip()
        name = get_element_text(driver, (By.XPATH, create_xpath('Name/Address')))
        name = name.split('\n')[0].strip() if "\n" in name else name.strip()
        quantity = get_element_text(driver, (By.XPATH, f"{create_xpath('Products')}//td[1]")).strip()
        product_code = get_element_text(driver, (By.XPATH, f"{create_xpath('Products')}//td[2]")).strip()
        course_name = get_element_text(driver, (By.XPATH, f"{create_xpath('Products')}//td[3]")).strip()
        return training_site, name, quantity, product_code, course_name
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
        click_element_by_js(driver, (By.ID, "btnConfirm"))
        time.sleep(2)
        click_element_by_js(driver, (By.ID, "btnComplete"))
    except Exception as e:
        print(f"Error assigning to instructor: {e}")
        pass

def assign_to_training_center(driver, quantity, product_code, training_site):
    try:
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