from Utils.functions import *


driver = get_undetected_driver()
login_to_enrollware_and_navigate_to_tc_product_orders(driver)
rows_to_process = get_indexes_to_process(driver)
for index in rows_to_process:
    try:
        time.sleep(2)
        click_element_by_js(driver, (By.XPATH, f"//tbody/tr[{index}]/td[7]/a"))
        training_site, name, quantity, product_code, course_name = get_order_data(driver)
        if 'red cross' in course_name.lower() or 'redcross' in course_name.lower():
            print(f"Skipping Red Cross course: {course_name}")
            click_element_by_js(driver, (By.ID, "mainContent_backButton"))
            continue
        if not available_courses.is_course_available(product_code):
            print(f"Course {product_code} is not available for eCard generation.")
            click_element_by_js(driver, (By.ID, "mainContent_backButton"))
            continue
        # open a new tab
        driver.execute_script("window.open('');")
        # switch to the new tab
        driver.switch_to.window(driver.window_handles[-1])
        login_to_atlas(driver)
        navigate_to_eCard_section(driver)
        time.sleep(2)
        sign_in_button = check_element_exists(driver, (By.XPATH, "(//button[text()= 'Sign In | Sign Up'])[1]"))
        if sign_in_button:
            login_to_atlas(driver)
            navigate_to_eCard_section(driver)
        # switch to the next tab
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(2)
        available_course_selector = f"//td[contains(text(), '{product_code}')]/preceding-sibling::td[@role='button']"
        available_course = check_element_exists(driver, (By.XPATH, available_course_selector))
        if not available_course:
            course_not_available(driver, product_code)
            continue
        available_qyt_on_ecard = get_element_text(driver, (By.XPATH, f"//td[contains(text(), '{product_code}')]/preceding-sibling::td[1]"))
        if int(available_qyt_on_ecard) < int(quantity):
            qyt_not_available(driver, product_code, available_qyt_on_ecard, quantity)
            continue
        click_element_by_js(driver, (By.XPATH, available_course_selector))
        assignment_site = "Assign to Instructor" if "615-230-7991" in training_site else "Assign to Training Site"
        if assignment_site == "Assign to Instructor":
            assign_to_instructor(driver, name, quantity, product_code)
        elif assignment_site == "Assign to Training Site":
            code = training_site.split(' ')[0].strip() if ' ' in training_site else training_site.strip()
            training_site = get_training_site_name(code)
            assign_to_training_center(driver, quantity, product_code, training_site)
        else:
            print("Unknown assignment site. Skipping this order.")
            go_back(driver)
            click_element_by_js(driver, (By.ID, "mainContent_backButton"))
            continue
        print(f"Successfully processed row {index}: {name}, {product_code}, {course_name}")
        go_back(driver)
        mark_order_as_complete(driver)
    except Exception as e:
        print(f"Error processing row {index}: {e}")
        continue
