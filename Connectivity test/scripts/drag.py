import logging

import time
from selenium.webdriver.common.action_chains import ActionChains
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def tap_and_hold(driver, xpath, hold_duration=2):
    """
    Tap and hold on an element for a specified duration.

    Args:
        driver: Appium driver instance
        xpath: XPath of the element to tap and hold
        hold_duration: Duration to hold in seconds (default: 2)
    """
    delta = 10
    element = WebDriverWait(driver, delta).until(
        EC.presence_of_element_located((AppiumBy.XPATH, xpath))
    )
    action = ActionChains(driver)
    action.click_and_hold(element)
    action.pause(hold_duration)
    action.release()
    action.perform()


def tap_hold_and_drag(
    driver, src_xpath, dest_xpath, hold_duration=1, move_duration=1000
):
    delta = 10
    src_ele = WebDriverWait(driver, delta).until(
        EC.presence_of_element_located((AppiumBy.XPATH, src_xpath))
    )
    dest_ele = WebDriverWait(driver, delta).until(
        EC.presence_of_element_located((AppiumBy.XPATH, dest_xpath))
    )
    action = ActionChains(driver, duration=move_duration)
    action.click_and_hold(src_ele)
    action.pause(hold_duration)
    action.move_to_element(dest_ele)
    action.release()
    action.perform()


def run(driver):
    # delta = 10
    src_xpath = '(//android.widget.RelativeLayout[@resource-id="com.medtronic.neuro.dbs.clinician:id/gpc_first_left_program"])[1]'
    dest_xpath = '//android.widget.LinearLayout[@resource-id="com.medtronic.neuro.dbs.clinician:id/ll_group_trash_area"]'
    tap_hold_and_drag(
        driver, src_xpath, dest_xpath, hold_duration=1, move_duration=3000
    )
    # src_ele = WebDriverWait(driver, delta).until(
    #     EC.presence_of_element_located((AppiumBy.XPATH, src_xpath))
    # )
    # dest_ele = WebDriverWait(driver, delta).until(
    #     EC.presence_of_element_located((AppiumBy.XPATH, dest_xpath))
    # )
    # action = ActionChains(driver, duration=1000)
    # action.click_and_hold(src_ele)
    # action.drag_and_drop(src_ele, dest_ele)
    # action.perform()
