import logging
import subprocess
import time


def run(driver):
    # commands = [
    #     "com.android.settings/.Settings",
    #     "com.adobe.reader/.AdobeReader",
    #     "com.airwatch.androidagent/com.airwatch.agent.Hub.hostactivity.HostActivity",
    #     "com.sec.android.gallery3d/com.samsung.android.gallery.app.activity.GalleryActivity",
    #     "com.sec.android.app.clockpackage/.ClockPackage",
    #     "com.sec.android.app.camera/.Camera",
    #     "com.airwatch.browser/.ui.SplashActivityNew",
    #     "com.sec.android.app.myfiles/.external.ui.MainActivity",
    #     "com.sec.android.app.popupcalculator/.Calculator",
    # ]
    pkgs = [
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
    udid = driver.capabilities["udid"]
    for pkg in pkgs:
        code = subprocess.run(f"adb -s {udid} shell am start -n {pkg}", shell=True)
        if code.returncode:
            logging.info(f"{pkg} doesn't exist")
            continue
        time.sleep(5)


if __name__ == "__main__":
    run("")
