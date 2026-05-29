import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def run(driver):
    delta = 10
    element = WebDriverWait(driver, delta).until(
        EC.presence_of_element_located(
            (
                AppiumBy.XPATH,
                '//android.widget.ImageButton[@resource-id="com.medtronic.neuro.tango.patient:id/btn_up_arrow"]',
            )
        )
    )
    element.click()
    time.sleep(1)
    element = WebDriverWait(driver, delta).until(
        EC.presence_of_element_located(
            (
                AppiumBy.XPATH,
                '//android.widget.ImageButton[@resource-id="com.medtronic.neuro.tango.patient:id/btn_down_arrow"]',
            )
        )
    )
    element.click()
