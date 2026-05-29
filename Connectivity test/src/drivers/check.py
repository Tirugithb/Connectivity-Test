from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Check wheather the element is present
def check(driver, ele_xpath, delta) -> bool:
    try:
        WebDriverWait(driver, delta).until(
            EC.visibility_of_element_located((AppiumBy.XPATH, ele_xpath))
        )
        return True
    except:
        return False
