import logging
import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def run(driver):
    delta = 10
    # time.sleep(300)
    flag = False
    while True:
        switch_btn = WebDriverWait(driver, delta).until(
            EC.presence_of_element_located(
                (
                    AppiumBy.XPATH,
                    '//android.widget.ImageButton[@resource-id="com.medtronic.neuro.scspatient.painrcapp:id/switch_group_icon"]',
                )
            )
        )
        switch_btn.click()
        # logging.info("Sleeping for 5 Minutes")
        if not flag:
            grp_change = WebDriverWait(driver, delta).until(
                EC.presence_of_element_located(
                    (
                        AppiumBy.XPATH,
                        '//android.widget.Button[@content-desc="PRS Off" and @text="Group C"]',
                    )
                )
            )
            grp_change.click()
        else:
            grp_change = WebDriverWait(driver, delta).until(
                EC.presence_of_element_located(
                    (
                        AppiumBy.XPATH,
                        '//android.widget.Button[@content-desc="PRS Off" and @text="Group B"]',
                    )
                )
            )
            grp_change.click()
        try:
            loader = WebDriverWait(driver, 1, poll_frequency=0.1).until(
                EC.presence_of_element_located(
                    (
                        AppiumBy.XPATH,
                        "//android.widget.ImageView",
                    )
                )
            )
            logging.info(loader)
        except:
            logging.info("Not found")
        flag = not flag
