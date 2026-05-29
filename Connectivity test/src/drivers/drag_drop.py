from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from src.drivers.search import search


# Dynamic drag and drop
def drag_drop(src, dest, driver):
    con_xpath = "//android.widget.ExpandableListView"
    ele_xpath = f"//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextView[@text='{src}']"
    search(con_xpath, src, driver)
    src_ele = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((AppiumBy.XPATH, ele_xpath))
    )
    search(con_xpath, dest, driver)
    ele_xpath = (
        f"//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextView[@text='{dest}']"
    )
    dest_ele = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((AppiumBy.XPATH, ele_xpath))
    )
    action = ActionChains(driver, duration=1000)
    action.drag_and_drop(src_ele, dest_ele)
    action.perform()
