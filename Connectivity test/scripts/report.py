from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def run(driver, *args):
    delta = 10
    element = WebDriverWait(driver, delta).until(
        EC.presence_of_element_located(
            (
                AppiumBy.XPATH,
                # '(//android.widget.LinearLayout[@resource-id="com.medtronic.neuro.intellisapp:id/result_text_container"])[1]',
                "(//android.widget.LinearLayout[contains(@resource-id,'result_text_container')])[1]",
            )
        )
    )
    element.click()
    index = int(args[0][0])
    # print(
    #     f'(//android.widget.ImageButton[contains(@resource-id, "row_icon")])[{index}]'
    # )
    dwn_btn = WebDriverWait(driver, delta).until(
        EC.presence_of_element_located(
            (
                AppiumBy.XPATH,
                f'(//android.widget.ImageButton[contains(@resource-id, "row_icon")])[{index}]',
            )
        )
    )
    dwn_btn.click()
