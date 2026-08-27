from selenium.webdriver.common.by import By


class EnrollwareLoginPage:
    username_input = (By.ID, "username")
    password_input = (By.ID, "password")
    remember_me_checkbox = (By.ID, "rememberMe")
    login_button = (By.ID, "login-button")

class EnrollwareOrderPage:
    order_data = lambda x: (By.XPATH, f"//label[text()= '{x}']/parent::div/following-sibling::div")
    order_status_select = (By.ID, "mainContent_status")
    status_update_button = (By.ID, "mainContent_statusUpdateBtn")
    email_button = (By.ID, "mainContent_emailBtn")
    send_email_button = (By.ID, "mainContent_sendButton")
    back_button = (By.ID, "mainContent_backButton")
    course_record_entry = (By.ID, "assign")

class AHALoginPage:
    sign_in_link = (By.XPATH, "(//button[text()= 'Sign In | Sign Up'])[1]")
    username_input = (By.ID, "Email")
    password_input = (By.ID, "password")
    sign_in_button = (By.ID, "login-button")

class AHAInventoryPage:
    available_course_selector = lambda x: (By.XPATH, f"//td[contains(text(), '{x}')]/preceding-sibling::td")
    assign_to = lambda x: (By.XPATH, f"//div/a[contains(text(), Assign to {x})]")
    finish_button = (By.ID, "btnComplete")
    go_to_inventory_button = (By.XPATH, "//a[text()= 'Go To Inventory']")

class AssignToInstructorPage:
    role_select = (By.ID, "RoleId")
    course_select = (By.ID, "CourseId")
    training_center_select = (By.ID, "ddlTC")
    training_site_select = (By.ID, "ddlSite")
    instructor_select = (By.XPATH, "//select[@id= 'assignTo']/following-sibling::div/button")
    instructor_name_selector = lambda x: (By.XPATH, f"(//label[contains(text(), '{x}')])[1]")
    submit_button = (By.ID, "btnMoveNext")
    quantity_input = (By.ID, "qty1")
    available_quantity = (By.ID, "tdAvailQty")
    continue_button = (By.ID, "btnConfirm")

class AssignToTrainingCenterPage:
    training_center_select = (By.ID, "tcId")
    training_site_select = (By.ID, "tsList")
    course_select = (By.ID, "courseId")
    submit_button = (By.ID, "btnValidate")
    quantity_input = (By.ID, "qty")

class ShopCPRPage:
    sign_in_link = (By.XPATH, "//a[contains(@href, 'login')]")
    sign_in_button = (By.ID, "btnSignIn")
    popup_form = (By.XPATH, "//div[@id= 'org-form']")
    popup_form_continue_button = (By.XPATH, "//button[text()= 'Continue']")
    cart_count = (By.CLASS_NAME, "scpr-cartcount")
    show_cart_button = (By.ID, "aha-showcart")
    delete_item_button = (By.ID, "remove-product")
    empty_cart_message = (By.XPATH, "//p[contains(text(), 'You have no items in your shopping cart.')]")
    course_cards_link = (By.XPATH, "//span[text()= 'Course Cards']/parent::a")
    heart_saver_bundles_link = (By.XPATH, "//span[text()= 'Heartsaver Bundles']/parent::a")
    products_elements = (By.XPATH, "(//div[@data-container= 'product-list'])[1]")
    search_product_button = (By.XPATH, "//button[@title= 'Search Product']")
    search_input = (By.XPATH, "//input[@id= 'searchtext']")
    search_button = (By.XPATH, "//button[@id= 'btnsearch']")
    view_details_button = (By.XPATH, "//a[@title= 'View Details']")
    add_to_cart_button = (By.XPATH, "//button[@id= 'bundle-slide']")
    cart_quick_view = (By.XPATH, "//a[contains(@id, 'title-quick-view')]")
    quantity_input = (By.CSS_SELECTOR, "input[id=qty]")
    add_to_cart_button_2 = (By.CSS_SELECTOR, "button[id=product-addtocart-button]")
    cart_wrapper = (By.ID, "minicart-content-wrapper")
    show_cart_button_2 = (By.XPATH, "//a[@id= 'aha-showcart']")
    checkout_button = (By.ID, "top-cart-btn-checkout")
    attention_message = (By.XPATH, "//span[contains(text(), 'requires attention')]")
    security_id_input = (By.XPATH, "//input[@id= 'sid']")
    proceed_checkout = (By.ID, "proceed-checkout")
    tax_status = (By.ID, "taxStatus")
    training_site_select = lambda x: (By.XPATH, f"//a[contains(text(), '{x}')]")
    continue_purchase = (By.ID, "purchase-continue-btn")
    po_number_input = (By.ID, "po_number")
    proceed_to_payment = (By.XPATH, "//button[text()= 'Proceed to Payment']")
