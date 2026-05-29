from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Check for element and click on it
def ele_id(driver, ele_id, delta):
    element = WebDriverWait(driver, delta).until(
        EC.presence_of_element_located((AppiumBy.id, ele_id))
    )
    element.click()
