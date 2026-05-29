import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.drivers.check import check


def gib_element(driver, delta) -> int:
    element = WebDriverWait(driver, delta).until(
        EC.presence_of_element_located(
            (
                AppiumBy.XPATH,
                '//android.widget.LinearLayout[@resource-id="com.medtronic.neuro.tango.clinician:id/switcher_container"]',
            )
        )
    )
    arr = element.find_elements(
        AppiumBy.XPATH, "//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextView"
    )
    val = int("".join(item.get_attribute("text") for item in arr))
    return val


def run(driver):
    delta = 10
    while gib_element(driver, delta) != 80:
        element = WebDriverWait(driver, delta).until(
            EC.presence_of_element_located(
                (
                    AppiumBy.XPATH,
                    '//android.widget.ImageButton[@resource-id="com.medtronic.neuro.tango.clinician:id/btn_up_arrow"]',
                )
            )
        )
        element.click()
        time.sleep(0.5)

    while gib_element(driver, delta) != 60:
        element = WebDriverWait(driver, delta).until(
            EC.presence_of_element_located(
                (
                    AppiumBy.XPATH,
                    '//android.widget.ImageButton[@resource-id="com.medtronic.neuro.tango.clinician:id/btn_down_arrow"]',
                )
            )
        )
        element.click()
        time.sleep(0.5)
