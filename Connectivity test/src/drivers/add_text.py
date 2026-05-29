from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Write text on textbox
def add_text(driver, ele_xpath, delta, input):
    if ele_xpath.startswith('//'):
        text_box = WebDriverWait(driver, delta).until(
            EC.presence_of_element_located((AppiumBy.XPATH, ele_xpath))
        )
    else:
        try:
            text = WebDriverWait(driver, delta).until(
                EC.presence_of_element_located(
                    (
                        AppiumBy.XPATH,
                        f'//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextLabel[@text="{ele_xpath}"]/..',
                        # '//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextLabel[@text="FIRST NAME * "]/..',
                        # '//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextLabel[@text="FIRST NAME * "]/..',
                    )
                )
            )
        except:
            text = WebDriverWait(driver, delta).until(
                EC.presence_of_element_located(
                    (
                        AppiumBy.XPATH,
                        f'//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextView[@text="{ele_xpath}"]/..',
                        # '//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextLabel[@text="FIRST NAME * "]/..',
                        # '//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextLabel[@text="FIRST NAME * "]/..',
                    )
                )
            )

        text_box = text.find_element(
            AppiumBy.XPATH, "//com.medtronic.neuro.HarmonyUI.widget.HarmonyEditText"
        )
    # text.find_element()
    text_box.clear()
    text_box.send_keys(input)
    # element = WebDriverWait(driver, delta).until(
    #     EC.presence_of_element_located((AppiumBy.XPATH, ele_xpath))
    # )
    # element.send_keys(input)
