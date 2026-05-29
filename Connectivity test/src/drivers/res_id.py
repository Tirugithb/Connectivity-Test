from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Check for element and click on it
def res_id(driver, ele_xpath, delta):
    element = WebDriverWait(driver, delta).until(
        EC.presence_of_element_located((AppiumBy.ID, ele_xpath))
    )
    element.click()
