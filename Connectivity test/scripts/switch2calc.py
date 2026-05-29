from random import randrange
import subprocess
import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# from src.drivers.toggle import toggle


def run(driver):
    pkg = [
        "com.sec.android.app.popupcalculator/.Calculator",
        "com.adobe.reader/.AdobeReader",
        "com.sec.android.app.clockpackage/.ClockPackage",
        "com.sec.android.gallery3d/com.samsung.android.gallery.app.activity.GalleryActivity",
        "com.sec.android.app.myfiles/.external.ui.MainActivity",
        "com.android.vending/.AssetBrowserActivity",
        "com.android.settings/.Settings",
        "com.airwatch.browser/.MainActivity",
        "com.airwatch.contentlocker/.login.LoginManagerActivity",
        "com.airwatch.androidagent/.ORIGINAL",
        "com.sec.android.app.camera/.Camera",
    ]
    rand_num = randrange(len(pkg))
    udid = driver.capabilities["udid"]
    subprocess.run(f"adb -s {udid} shell am start -n {pkg[rand_num]}", shell=True)
    time.sleep(5)
    driver.press_keycode(187)
    driver.press_keycode(187)
    time.sleep(5)
    # app_init = subprocess.run(f"adb shell am start -n {pkg}", shell=True)
    # delta = 10
    # toggle(driver, '//android.widget.Button[@text="1"]', delta)
    # toggle(driver, '//android.widget.Button[@text="+"]', delta)
    # toggle(driver, '//android.widget.Button[@text="1"]', delta)
    # toggle(driver, '//android.widget.Button[@text="="]', delta)


if __name__ == "__main__":
    run("")
