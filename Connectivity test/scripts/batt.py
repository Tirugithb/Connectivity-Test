import logging
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
                '//android.widget.LinearLayout[@resource-id="com.medtronic.neuro.scspatient.painrcapp:id/action_bar_battery"]',
            )
        )
    )
    element.click()
    ins = WebDriverWait(driver, delta).until(
        EC.presence_of_element_located(
            (
                AppiumBy.XPATH,
                '//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextView[@resource-id="com.medtronic.neuro.scspatient.painrcapp:id/tv_ins_battery_status"]',
            )
        )
    )
    ins_batt = ins.get_attribute("text")
    comm = WebDriverWait(driver, delta).until(
        EC.presence_of_element_located(
            (
                AppiumBy.XPATH,
                '//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextView[@resource-id="com.medtronic.neuro.scspatient.painrcapp:id/tv_communicator_battery_status"]',
            )
        )
    )
    comm_batt = comm.get_attribute("text")
    logging.info(f"\nINS battery: {ins_batt}\nCOMM battery: {comm_batt}")
