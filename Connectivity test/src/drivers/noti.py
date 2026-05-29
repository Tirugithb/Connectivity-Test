# from configs.capabilitites import TIME_UNTIL
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Opens up Notifiction panel
def noti(driver):
    # print(driver.get_window_size())
    width = driver.get_window_size()["width"]
    driver.swipe(width / 2, 25, width / 2, 750)
