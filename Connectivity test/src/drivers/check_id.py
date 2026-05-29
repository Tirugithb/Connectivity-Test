import logging
import time
from appium.webdriver.webdriver import WebDriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Check wheather the element is present
def check_id(driver: WebDriver, ele_xpath, delta) -> bool:
    try:
        activity = (
            # "com.medtronic.neuro.SMPlusPatient.userinterface.activities.PatientActivity"
            ".userinterface.activities.PatientActivity"
        )
        # logging.info(activity)

        logging.info(driver.wait_activity(activity, 180))
        WebDriverWait(driver, delta).until(
            # EC.visibility_of_element_located(
            #     (
            #         AppiumBy.ID,
            #         "com.medtronic.neuro.SMPlusPatient:id/connecting_circle_widget",
            #     )
            # )
            EC.visibility_of_element_located((AppiumBy.ID, ele_xpath))
        )
        return True
    except Exception as e:
        logging.info(e)
        return False
