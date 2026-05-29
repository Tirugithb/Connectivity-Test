import csv
from datetime import datetime
import importlib
import os
from pathlib import Path
import subprocess
import sys
import time
from tkinter import W
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import logging
from src.drivers.noti import noti
from src.drivers.qs import qs
from src.drivers.screenshot import screenshot
from src.drivers.check import check
from src.drivers.check_id import check_id
from src.drivers.add_text import add_text
from src.drivers.switch import switch
from src.drivers.scroll import scroll
from src.drivers.toggle import toggle
from src.drivers.tap import tap
from src.drivers.search import search
from src.drivers.drag_drop import drag_drop
from src.drivers.res_id import res_id


def load_script(script_name, function_name=None, *args, **kwargs):
    """Load a Python script and optionally call a function with arguments"""
    # Get the absolute path to the project root (parent of src directory)
    project_root = Path(__file__).resolve().parent.parent
    script_path = project_root / "scripts" / f"{script_name}.py"

    # Log for debugging
    logging.info(f"Project root: {project_root}")
    logging.info(f"Looking for script at: {script_path}")
    logging.info(f"Script exists: {script_path.exists()}")

    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    spec = importlib.util.spec_from_file_location(script_name, script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # If function_name is provided, call it with the arguments
    if function_name:
        if not hasattr(module, function_name):
            raise AttributeError(
                f"Function '{function_name}' not found in script '{script_name}'"
            )

        func = getattr(module, function_name)
        return func(*args, **kwargs)

    return module


def evaluate_condition(condition, driver, timeout=5):
    """
    Evaluate a condition and return True/False

    Args:
        condition: Dictionary containing condition details
        driver: Appium driver instance
        timeout: Timeout for element checks

    Returns:
        bool: True if condition is met, False otherwise
    """
    try:
        condition_type = condition.get("type")

        if condition_type == "check_text":
            text = condition.get("text")
            ele_xpath = f'//*[@text = "{text}"]'
            try:
                element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((AppiumBy.XPATH, ele_xpath))
                )
                result = element is not None
                logging.info(f"Condition check_text('{text}'): {result}")
                return result
            except TimeoutException:
                logging.info(f"Condition check_text('{text}'): False (timeout)")
                return False

        elif condition_type == "element_exists":
            xpath = condition.get("xpath")
            try:
                element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((AppiumBy.XPATH, xpath))
                )
                result = element is not None
                logging.info(f"Condition element_exists('{xpath}'): {result}")
                return result
            except TimeoutException:
                logging.info(f"Condition element_exists('{xpath}'): False (timeout)")
                return False

        elif condition_type == "element_visible":
            text = condition.get("text")
            ele_xpath = f'//*[@text = "{text}"]'
            try:
                element = WebDriverWait(driver, timeout).until(
                    EC.visibility_of_element_located((AppiumBy.XPATH, ele_xpath))
                )
                result = element.is_displayed()
                logging.info(f"Condition element_visible('{text}'): {result}")
                return result
            except (TimeoutException, NoSuchElementException):
                logging.info(f"Condition element_visible('{text}'): False")
                return False

        # elif condition_type == "element_enabled":
        #     text = condition.get("text")
        #     ele_xpath = f'//*[@text = "{text}"]'
        #     try:
        #         element = WebDriverWait(driver, timeout).until(
        #             EC.presence_of_element_located((AppiumBy.XPATH, ele_xpath))
        #         )
        #         result = element.is_enabled()
        #         logging.info(f"Condition element_enabled('{text}'): {result}")
        #         return result
        #     except (TimeoutException, NoSuchElementException):
        #         logging.info(f"Condition element_enabled('{text}'): False")
        #         return False

        else:
            logging.warning(f"Unknown condition type: {condition_type}")
            return False

    except Exception as e:
        logging.error(f"Error evaluating condition: {e}")
        return False


def process_conditional_step(item, driver, therapy):
    """
    Process a conditional step (if/else)

    Args:
        item: Conditional step dictionary
        driver: Appium driver instance
        therapy: Current therapy name
    """
    condition = item.get("condition")
    then_steps = item.get("then_steps", [])
    else_steps = item.get("else_steps", [])

    logging.info(f"Processing conditional: {condition}")

    # Evaluate the condition
    condition_result = evaluate_condition(condition, driver)

    # Execute appropriate steps based on condition result
    if condition_result:
        logging.info("Condition is TRUE - executing THEN steps")
        steps_to_execute = then_steps
    else:
        logging.info("Condition is FALSE - executing ELSE steps")
        steps_to_execute = else_steps

    # Process the selected steps
    if steps_to_execute:
        # Create a temporary query structure for processing
        temp_query = {
            "name": f"conditional_execution_{condition_result}",
            "steps": steps_to_execute,
        }

        # Process the steps recursively
        process_queries_beta([temp_query], driver, therapy)
    else:
        logging.info("No steps to execute for this condition branch")


def process_queries_beta(queries, driver, therapy) -> None:
    timestamp = {}
    temp_arr = []
    try:
        for query in queries:
            for item in query["steps"]:
                optional = item["optional"]
                item["udid"] = driver.capabilities["udid"]
                logging.info(json.dumps(item, indent=4))
                offset_x, offset_y = 0, 0
                flag = 0
                delta = item["time"]

                try:
                    # activity = "com.medtronic.neuro.SMPlusPatient/.userinterface.activities.PatientActivity"
                    # logging.info(driver.wait_activity(activity, 180))
                    match item["type"]:
                        case "scroll":
                            scroll(driver, int(item["text"]))
                        case "conditional":
                            # Handle if/else statements
                            process_conditional_step(item, driver, therapy)

                        case "script":
                            arr = item["text"].split(",")
                            # print(arr)
                            my_script = load_script(arr[0])
                            # my_script = load_script(item["text"])
                            if len(arr) > 1:
                                my_script.run(driver, arr[1:])
                            else:
                                my_script.run(driver)

                        case "noti":
                            noti(driver)

                        case "qs":
                            ele_xpath = '//android.view.ViewGroup[@resource-id="com.android.systemui:id/tile_page"]'
                            qs(driver, ele_xpath, item["text"], item["enable"])

                        case "next":
                            ele_xpath = '//android.widget.ImageView[contains(@resource-id, "next")]'
                            flag = 1

                        case "back":
                            driver.back()

                        case "exec":
                            code = subprocess.run(
                                item["text"], shell=True
                            )  # Execution of shell commands
                            if code.returncode:
                                logging.info(f"{item['text']} doesn't exist")

                        case "delay":
                            time.sleep(item["text"] * 60)

                        case "delta":
                            if not timestamp.get(item["text"]):
                                timestamp[item["text"]] = time.perf_counter()
                            else:
                                logging.info(
                                    f"{item['text']} {time.perf_counter() - timestamp[item['text']]}"
                                )
                                temp_arr.append(
                                    time.perf_counter() - timestamp[item["text"]]
                                )
                                timestamp[item["text"]] = None

                        case "check_raw":
                            # ele_xpath = f'//*[{item["text"]}]'
                            ele_xpath = item["text"]
                            vlad = check(driver, ele_xpath, delta)
                            logging.info(f"checking {ele_xpath} : {vlad}")

                        case "checkid":
                            ele_xpath = item["text"]
                            # ele_xpath = f'//*[@text = "{item["text"]}"]'
                            vlad = check_id(driver, ele_xpath, delta)
                            logging.info(f"checking {ele_xpath} : {vlad}")
                        case "check":
                            ele_xpath = f'//*[@text = "{item["text"]}"]'
                            vlad = check(driver, ele_xpath, delta)
                            logging.info(f"checking {ele_xpath} : {vlad}")
                            if not vlad:
                                raise ValueError(
                                    f"Element with text '{item['text']}' not found"
                                )

                        case "radio_button":
                            if item["resource_id"] is not None:
                                ele_xpath = f"//android.widget.RadioButton[contains(@resource-id, '{item['resource_id']}') and @text='{item['text']}']"
                            else:
                                ele_xpath = f"//android.widget.RadioButton[@text='{item['text']}']"
                            flag = 1

                        case "button":
                            time.sleep(1)
                            ele_xpath = (
                                f"//android.widget.Button[@text='{item['text']}']"
                            )
                            flag = 1

                        case "chevron":
                            # flag = 1
                            offset_y = 85
                            flag = 0
                            try:
                                ele_xpath = f"//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextLabel[contains(@text,'{item['text']}')]"
                                toggle(driver, ele_xpath, delta, 10, offset_y)
                            except:
                                ele_xpath = f"//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextView[contains(@text,'{item['text']}')]"
                                toggle(driver, ele_xpath, delta, 10, offset_y)

                        case "chevron_offset":
                            ele_xpath = f"//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextView[@text='{item['text']}']"
                            flag = 1
                            offset_x, offset_y = 150, 100

                        case "tap":
                            x, y = item["text"].split(",")
                            tap(x, y, driver)

                        case "add_text":
                            # ele_xpath = f"//com.medtronic.neuro.HarmonyUI.widget.HarmonyEditText[contains(@resource-id, '{item['text']}')]"
                            # print(ele_xpath)
                            # add_text(driver, ele_xpath, delta, item["input"])
                            add_text(driver, item["text"], delta, item["input"])

                        case "dropdown":
                            con_xpath = "//android.widget.LinearLayout[contains(@resource-id, 'spinner_drop_down')]"
                            ele_xpath = f"//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextView[@text='{item['text']}']"
                            flag = 1
                            search(con_xpath, item["text"], driver)

                        case "linear_layout":
                            ele_xpath = f"//android.widget.RelativeLayout[@content-desc='{item['content_desc']}']"
                            flag = 1

                        case "electrode_placement":
                            ele_xpath = f"//com.medtronic.neuro.paincommon.view.programming.widgets.leadworkarea.ElectrodeShape[@content-desc='Electrode_Shape_Index_{item['index']}']"
                            flag = 1

                        case "resid":
                            _id = item["text"]
                            res_id(driver, _id, delta)
                            flag = 0

                        case "xpath":
                            ele_xpath = item["text"]
                            flag = 1

                        case "switch":
                            if item["text"].startswith("//"):
                                ele_xpath = item["text"]
                            else:
                                ele_xpath = f"//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextView[@text = '{item['text']}']"
                            switch(ele_xpath, item["enable"], driver)

                        case "checkbox":
                            ele_xpath = f"//com.medtronic.neuro.HarmonyUI.widget.HarmonyCheckBox[@text = '{item['text']}']"
                            flag = 1
                        case "swipe":
                            cord = item["text"].split(" ")
                            driver.swipe(cord[0], cord[1], cord[2], cord[3], 750)
                        case "drag_drop":
                            drag_drop(item["source"], item["destination"], driver)

                        case "text_view":
                            ele_xpath = [
                                f"//com.medtronic.neuro.HarmonyUI.widget.HarmonyTextView[@text='{item['text']}']",
                                f'//android.widget.TextView[@text="{item['text']}"]',
                                f"//com.medtronic.neuro.harmonyui.widget.HarmonyTextView[@text='{item['text']}']",
                            ]
                            # text_change_flag = False
                            for xpath_item in ele_xpath:
                                try:
                                    toggle(
                                        driver, xpath_item, delta, offset_x, offset_y
                                    )
                                    break
                                except:
                                    logging.info("Text type different")
                                    delta = 2
                                    continue

                        case "next_track":
                            ele_xpath = '//android.widget.ImageView[contains(@resource-id, "next_track")]'
                            flag = 1

                        case "prev_track":
                            ele_xpath = '//android.widget.ImageView[contains(@resource-id, "prev_track")]'
                            flag = 1

                        case "fw":
                            ele_xpath = '//android.widget.ImageButton[contains(@resource-id, "programming_btn_forward")]'
                            # ele_xpath = '//android.widget.ImageButton[@resource-id="com.medtronic.neuro.scscptrialing:id/programming_btn_forward"]'
                            flag = 1

                        case "bk":
                            ele_xpath = '//android.widget.ImageButton[contains(@resource-id, "programming_btn_previous")]'
                            # ele_xpath = '//android.widget.ImageButton[@resource-id="com.medtronic.neuro.scscptrialing:id/programming_btn_previous"]'
                            flag = 1

                        case "h_toggle":
                            ele_xpath = "//com.medtronic.neuro.HarmonyUI.widget.HarmonyToggleButton"
                            # ele_xpath = '//android.widget.ImageButton[@resource-id="com.medtronic.neuro.scspatient.painpcapp:id/btn_adjust_therapy_up"]'
                            flag = 1
                        case "up":
                            ele_xpath = '//android.widget.ImageButton[contains(@resource-id, "btn_adjust_therapy_up")]'
                            # ele_xpath = '//android.widget.ImageButton[@resource-id="com.medtronic.neuro.scspatient.painpcapp:id/btn_adjust_therapy_up"]'
                            flag = 1

                        case "down":
                            ele_xpath = '//android.widget.ImageButton[contains(@resource-id, "btn_adjust_therapy_down")]'
                            # ele_xpath = '//android.widget.ImageButton[@resource-id="com.medtronic.neuro.scspatient.painpcapp:id/btn_adjust_therapy_down"]'
                            flag = 1

                        case "setting":
                            ele_xpath = '//android.widget.ImageView[@content-desc="More options"]'
                            flag = 1

                        case "setting2":
                            ele_xpath = (
                                "//com.medtronic.neuro.HarmonyUI.widget.HarmonySpinner"
                            )
                            flag = 1
                        case "display_icon":
                            ele_xpath = "(//android.widget.ImageButton[@resource-id='com.medtronic.neuro.painpcapp:id/row_icon'])[1]"
                            flag = 1
                        case "print":
                            logging.info(f'FROM SYSTEM: {item["text"]}')
                        case "screenshot":
                            if item["text"] != "":
                                # data = f"{driver.capabilities['udid']} {therapy} {item['text']}"
                                data = f"{item['text']}"

                            else:
                                # data = f"{datetime.now()}"
                                data = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                            # logging.info(data)
                            screenshot(
                                driver,
                                data,
                                # f"{driver.capabilities['udid']} {therapy} {item['text']}",
                            )

                        case "hamburger":
                            try:
                                ele_xpath = "//android.widget.ImageButton[@content-desc='Open navigation drawer']"
                                WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located(
                                        (AppiumBy.XPATH, ele_xpath)
                                    )
                                ).click()
                            except:
                                ele_xpath = (
                                    '//android.widget.ImageButton[@content-desc="DEMO"]'
                                )
                                WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located(
                                        (AppiumBy.XPATH, ele_xpath)
                                    )
                                ).click()
                            time.sleep(1)

                    if flag == 1:
                        toggle(driver, ele_xpath, delta, offset_x, offset_y)

                except Exception as e:
                    if optional:
                        logging.info("Optional query encountered")
                        continue
                    logging.info("Bruh moment")
                    screenshot(
                        driver, f"ERROR {datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}"
                    )
                    raise

    except Exception as e:
        logging.info("ERROR")
        logging.info(e)
        raise

    # if len(temp_arr) == 2:
    if len(temp_arr) == 1:
        file_exists = os.path.exists(f"temp {driver.capabilities['udid']}.csv")
        with open(
            f"temp {driver.capabilities['udid']}.csv", mode="a", newline=""
        ) as csv_file:
            # fieldnames = ["Timestamp", "Device to PTM DELTA", "PTM to INS DELTA"]
            fieldnames = ["Timestamp", "Resync delta"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()
            writer.writerow(
                {
                    "Timestamp": datetime.now(),
                    "Resync delta": temp_arr[0],
                    # "Device to PTM DELTA": temp_arr[0],
                    # "PTM to INS DELTA": temp_arr[1],
                }
            )
