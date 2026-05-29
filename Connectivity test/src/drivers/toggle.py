from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Check for element and click on it
def toggle(driver, ele_xpath, delta, offset_x=0, offset_y=0):
    element = WebDriverWait(driver, delta).until(
        EC.presence_of_element_located((AppiumBy.XPATH, ele_xpath))
    )
    if not offset_x and not offset_y:
        element.click()
    else:
        loc = element.location
        # print(loc)
        driver.tap([(loc["x"] + offset_x, loc["y"] + offset_y)])
