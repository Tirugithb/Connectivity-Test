from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Check wheather it is enabled, if not enable it (only for switch elements)
def switch(ele_xpath, enable, driver):
    try:
        ele_xpath = ele_xpath + "/.."
        parent = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((AppiumBy.XPATH, ele_xpath))
        )
        element = parent.find_element(AppiumBy.CLASS_NAME, "android.widget.Switch")
    except:
        ele_xpath = ele_xpath + "/../.."
        parent = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((AppiumBy.XPATH, ele_xpath))
        )
        element = parent.find_element(AppiumBy.CLASS_NAME, "android.widget.Switch")

    get_el = element.get_attribute("checked") == "true"
    if get_el == (not enable):
        element.click()
