from appium.webdriver.webdriver import WebDriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.drivers.search import search
from src.drivers.toggle import toggle


def run(driver: WebDriver):
    delta = 3
    con_xpath = (
        "//android.widget.LinearLayout[contains(@resource-id, 'spinner_drop_down')]"
    )
    ele = WebDriverWait(driver, 3).until(
        EC.presence_of_element_located(
            (
                AppiumBy.XPATH,
                '(//com.medtronic.neuro.HarmonyUI.widget.HarmonySpinner[@content-desc="not-pending"])[1]',
            )
        )
    )
    ele.click()
    search(con_xpath, "0", driver)
    toggle(
        driver,
        '//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextView[@text="0"]',
        delta,
        0,
        0,
    )
    ele = WebDriverWait(driver, 3).until(
        EC.presence_of_element_located(
            (
                AppiumBy.XPATH,
                '(//com.medtronic.neuro.HarmonyUI.widget.HarmonySpinner[@content-desc="not-pending"])[2]',
            )
        )
    )
    ele.click()
    search(con_xpath, "10", driver)
    toggle(
        driver,
        '//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextView[@text="10"]',
        delta,
        0,
        0,
    )

    ele = WebDriverWait(driver, 3).until(
        EC.presence_of_element_located(
            (
                AppiumBy.XPATH,
                '(//com.medtronic.neuro.HarmonyUI.widget.HarmonySpinner[@content-desc="not-pending"])[3]',
            )
        )
    )
    ele.click()
    search(con_xpath, "6", driver)
    toggle(
        driver,
        '//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextView[@text="6"]',
        delta,
        0,
        0,
    )

    ele = WebDriverWait(driver, 3).until(
        EC.presence_of_element_located(
            (
                AppiumBy.XPATH,
                '(//com.medtronic.neuro.HarmonyUI.widget.HarmonySpinner[@content-desc="not-pending"])[4]',
            )
        )
    )
    ele.click()
    search(con_xpath, "1", driver)
    toggle(
        driver,
        '//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextView[@text="1"]',
        delta,
        0,
        0,
    )

    ele = WebDriverWait(driver, 3).until(
        EC.presence_of_element_located(
            (
                AppiumBy.XPATH,
                '//com.medtronic.neuro.HarmonyUI.widget.HarmonySpinner[@resource-id="com.medtronic.neuro.SynchroMedPlus:id/hs_max_activation_number"]',
            )
        )
    )
    ele.click()
    search(con_xpath, "2", driver)
    toggle(
        driver,
        '//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextView[@text="2"]',
        delta,
        0,
        0,
    )
