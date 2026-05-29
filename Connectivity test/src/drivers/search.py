from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# searching on scrollable container
def search(ele_xpath, target, driver):
    container = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((AppiumBy.XPATH, ele_xpath))
    )
    size = container.size
    loc = container.location
    prev = ""
    flag = True
    while True:
        target_xpath = (
            f"//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextView[@text='{target}']"
        )
        try:
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((AppiumBy.XPATH, target_xpath))
            )
            # element.click()
            return
        except:
            curr = driver.page_source
            if prev == curr:
                flag = not flag
            if flag:
                driver.swipe(
                    loc["x"] + 10,
                    loc["y"] + size["height"] - 10,
                    loc["x"] + 10,
                    loc["y"] + (size["height"] / 2),
                )
            else:
                driver.swipe(
                    loc["x"] + 10,
                    loc["y"] + (size["height"] / 2),
                    loc["x"] + 10,
                    loc["y"] + size["height"] - 10,
                )
            prev = curr
