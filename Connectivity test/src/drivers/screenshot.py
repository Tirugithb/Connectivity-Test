from datetime import datetime
import logging
import os
import time


# Takes screenshot and saves it based on udid and appPackage subfolder
def screenshot(driver, name):
    time.sleep(3)
    screenshot_dir = rf"C:/Users/SVC-Systems-TestPC/Log_Screenshot_files/screenshots/{driver.capabilities['udid']}/{driver.capabilities['appPackage']}"
    os.makedirs(screenshot_dir, exist_ok=True)  # Ensure the directory exists
    # if name == "":
    #     name = datetime.now()
    base_filename = rf"{str(name)}.png"
    # logging.info(base_filename)
    file_path = os.path.join(screenshot_dir, base_filename)

    counter = 1
    while os.path.exists(file_path):
        file_path = os.path.join(screenshot_dir, f"{name}({counter}).png")
        counter += 1
    # full_path = os.path.abspath(file_path)
    # logging.info(f"Screenshot stored in {full_path} : PASSED")
    logging.info(f"Screenshot stored in {file_path} : PASSED")
    get_status = driver.get_screenshot_as_file(file_path)
    if not get_status:
        logging.info("Screenshot failed")
