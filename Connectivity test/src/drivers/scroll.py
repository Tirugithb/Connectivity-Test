import time
from appium.webdriver.webdriver import WebDriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def scroll(driver: WebDriver, val: int):
    # size = driver.get_window_size()
    con_xpath = '//androidx.viewpager.widget.ViewPager[@resource-id="com.medtronic.neuro.SynchroMedPlus:id/viewpager"]'
    container = WebDriverWait(driver, 3).until(
        EC.presence_of_element_located((AppiumBy.XPATH, con_xpath))
    )
    con_size = container.size
    y = con_size["height"] - 10
    x = (container.location)["x"]
    driver.swipe(x, y, x, y - (y * (val / 100)), 50)
    time.sleep(3)
