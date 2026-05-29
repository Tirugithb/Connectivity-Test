# from configs.capabilitites import TIME_UNTIL
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Opens up Quicksettings
def qs(driver, xpath, target, enabled):
    # print(driver.get_window_size())
    width = driver.get_window_size()["width"]
    while True:
        try:
            ele = driver.find_element(
                AppiumBy.XPATH,
                xpath,
            )
            break

        except:
            for _ in range(2):
                driver.swipe(width / 2, 25, width / 2, 750)
            continue

    flag = False

    while True:
        try:
            ele = driver.find_element(
                AppiumBy.XPATH,
                f'//android.view.ViewGroup[contains(@content-desc, "{target}")]',
            )
            break
        except:
            qs_panel_xpath = '//android.widget.LinearLayout[@resource-id="com.android.systemui:id/quick_settings_panel"]'
            qs_panel = WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((AppiumBy.XPATH, qs_panel_xpath))
            )
            size = qs_panel.size
            loc = qs_panel.location
            # if flag:
            #     driver.swipe(500, 700, 400, 700)  # 1100
            # else:
            #     driver.swipe(400, 700, 500, 700)
            if flag:
                driver.swipe(
                    loc["x"] + size["width"] - 25,
                    loc["y"] + size["height"] / 2,
                    loc["x"] + (size["width"] / 2),
                    loc["y"] + size["height"] / 2,
                )  # 1100
            else:
                driver.swipe(
                    loc["x"] + (size["width"] / 2),
                    loc["y"] + size["height"] / 2,
                    loc["x"] + size["width"] - 25,
                    loc["y"] + size["height"] / 2,
                )
            flag = not flag

    str = ele.get_attribute("content-desc")

    if ("Off" in str and enabled == True) or ("On" in str and enabled == False):
        ele.click()
    # driver.back()
