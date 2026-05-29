import logging
import subprocess
import time
from appium.webdriver.common.appiumby import AppiumBy

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.drivers.add_text import add_text
from src.drivers.switch import switch
from src.drivers.tap import tap


def run(driver):
    udid = driver.capabilities["udid"]
    code = subprocess.run(
        f"adb -s {udid} shell am start -n com.android.settings/.Settings", shell=True
    )  # Execution of shell commands
    if code.returncode:
        logging.info(f"Command failed with return code {code.returncode}")
    delta = 10
    time.sleep(3)
    tap(400, 100, driver)
    element = WebDriverWait(driver, delta).until(
        EC.presence_of_element_located(
            (
                AppiumBy.XPATH,
                '//android.widget.Button[@content-desc="Search"]',
            )
        )
    )
    element.click()
    add_text(
        driver,
        '//android.widget.EditText[@resource-id="com.android.settings.intelligence:id/search_src_text"]',
        delta,
        "software update",
    )

    element = WebDriverWait(driver, delta).until(
        EC.presence_of_element_located(
            (
                AppiumBy.XPATH,
                '//android.support.v7.widget.RecyclerView[@resource-id="com.android.settings.intelligence:id/list_results"]/android.widget.LinearLayout[1]',
            )
        )
    )
    element.click()
    switch(
        '//android.widget.TextView[@resource-id="android:id/title" and @text="Auto download over Wi-Fi"]',
        False,
        driver,
    )
    code = subprocess.run(
        f"adb shell input keyevent KEYCODE_APP_SWITCH", shell=True
    )  # Execution of shell commands
    if code.returncode:
        logging.info(f"Command failed with return code {code.returncode}")
    time.sleep(1)
    code = subprocess.run(
        f"adb shell input keyevent KEYCODE_APP_SWITCH", shell=True
    )  # Execution of shell commands
    if code.returncode:
        logging.info(f"Command failed with return code {code.returncode}")

    # for _ in range(2):
    #     code = subprocess.run(
    #         f"adb shell input keyevent KEYCODE_APP_SWITCH", shell=True
    #     )  # Execution of shell commands
    #     if code.returncode:
    #         logging.info(f"Command failed with return code {code.returncode}")
