import logging
import subprocess
import time
import threading
import os
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import urllib3
from src.processor_beta import process_queries_beta
from capabilities import capabilities
from src.parser_beta import parser_beta_driver

urllib3.disable_warnings()
logging.getLogger("urllib3").setLevel(logging.ERROR)


class PopupHandler:
    def __init__(self, driver):
        self.driver = driver
        self.monitoring = False
        self.monitor_thread = None

    def start_monitoring(self):
        """Start continuous popup monitoring in background"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_popups)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logging.info("Popup monitoring started")

    def stop_monitoring(self):
        """Stop popup monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        print("Popup monitoring stopped")

    def _monitor_popups(self):
        """Background thread to monitor and dismiss popups"""
        while self.monitoring:
            try:
                self.dismiss_common_popups()
                time.sleep(1)  # Check every 2 seconds
            except Exception as e:
                print(f"Error in popup monitoring: {e}")
                time.sleep(1)

    def dismiss_common_popups(self):
        """Dismiss common popup patterns"""
        popup_patterns = [
            # Common button texts
            ("xpath", "//android.widget.Button[@text='OK']"),
            ("xpath", "//android.widget.Button[@text='Allow']"),
            ("xpath", "//android.widget.Button[@text='Deny']"),
            ("xpath", "//android.widget.Button[@text='Cancel']"),
            ("xpath", "//android.widget.Button[@text='Not now']"),
            ("xpath", "//android.widget.Button[@text='Skip']"),
            ("xpath", "//android.widget.Button[@text='SKIP']"),
            # ("xpath", "//android.widget.Button[@text='Close']"),
            ("xpath", "//android.widget.Button[@text='Dismiss']"),
            ("xpath", "//android.widget.Button[@text='Continue']"),
            ("xpath", "//android.widget.Button[@text='Got it']"),
            # Resource IDs
            # ("id", "android:id/button1"),  # Default OK button
            # ("id", "android:id/button2"),  # Default Cancel button
            ("id", "com.android.packageinstaller:id/permission_allow_button"),
            ("id", "com.android.packageinstaller:id/permission_deny_button"),
            # Close buttons and X marks
            ("xpath", "//android.widget.ImageButton[@content-desc='Close']"),
            ("xpath", "//android.widget.ImageButton[@content-desc='Dismiss']"),
            ("xpath", "//android.widget.Button[@text='×']"),
            ("xpath", "//*[@text='×']"),
        ]

        for by_type, selector in popup_patterns:
            try:
                if by_type == "xpath":
                    element = self.driver.find_element(AppiumBy.XPATH, selector)
                elif by_type == "id":
                    element = self.driver.find_element(AppiumBy.ID, selector)

                if element and element.is_displayed():
                    element.click()
                    print(f"Dismissed popup: {selector}")
                    time.sleep(0.5)
                    return True
            except (NoSuchElementException, Exception):
                continue
        return False

    def handle_permission_popups(self):
        """Handle Android permission popups specifically"""
        permission_selectors = [
            "//android.widget.Button[contains(@text,'Allow') or contains(@text,'ALLOW')]",
            "//android.widget.Button[contains(@text,'Grant') or contains(@text,'GRANT')]",
            "//android.widget.Button[contains(@text,'OK') or contains(@text,'Ok')]",
            "//android.widget.Button[contains(@text,'Continue') or contains(@text,'CONTINUE')]",
        ]

        for selector in permission_selectors:
            try:
                element = self.driver.find_element(AppiumBy.XPATH, selector)
                if element and element.is_displayed():
                    element.click()
                    print(f"Granted permission: {selector}")
                    time.sleep(0.5)
                    return True
            except (NoSuchElementException, Exception):
                continue
        return False

    def detect_popup_by_layout(self):
        """Detect popups by analyzing screen layout"""
        dialog_selectors = [
            "//android.app.AlertDialog",
            "//android.app.Dialog",
            "//*[contains(@class,'AlertDialog')]",
            "//*[contains(@class,'Dialog')]",
            "//android.widget.PopupWindow",
        ]

        for selector in dialog_selectors:
            try:
                elements = self.driver.find_elements(AppiumBy.XPATH, selector)
                if elements and any(elem.is_displayed() for elem in elements):
                    return True
            except Exception:
                continue
        return False

    def handle_overlay_popups(self):
        """Handle overlay-type popups by clicking outside"""
        try:
            # Get screen dimensions
            screen_size = self.driver.get_window_size()
            width = screen_size["width"]
            height = screen_size["height"]

            # Try clicking at corners to dismiss overlays
            corners = [
                (50, 50),  # Top-left
                (width - 50, 50),  # Top-right
                (50, height - 50),  # Bottom-left
                (width - 50, height - 50),  # Bottom-right
            ]

            for x, y in corners:
                self.driver.tap([(x, y)])
                time.sleep(0.5)
                if not self.detect_popup_by_layout():
                    print(f"Dismissed overlay by tapping corner: ({x}, {y})")
                    return True

            return False
        except Exception as e:
            print(f"Error handling overlay popup: {e}")
            return False


def process_queries_with_popup_handling(parsed, driver, item, enable):
    """Wrapper for process_queries_beta with popup handling"""
    popup_handler = None

    if enable:
        popup_handler = PopupHandler(driver)

    try:
        if enable:
            # Start background popup monitoring
            popup_handler.start_monitoring()

            # Initial popup cleanup
            time.sleep(2)  # Wait for app to load
            popup_handler.dismiss_common_popups()
            popup_handler.handle_permission_popups()

        # Process your queries
        process_queries_beta(parsed, driver, item)

    except Exception as e:
        print(f"Error during query processing: {e}")
        if enable:
            # Try to recover by handling popups
            popup_handler.dismiss_common_popups()
            popup_handler.handle_overlay_popups()
        raise
    finally:
        if enable and popup_handler:
            # Stop popup monitoring
            popup_handler.stop_monitoring()


def get_first_device_id():
    """Get the first connected device ID from adb devices, throw error if none found"""
    try:
        result = subprocess.run(
            ["adb", "devices"], capture_output=True, text=True, check=True
        )

        # Parse output
        lines = result.stdout.strip().split("\n")

        # Skip header line "List of devices attached"
        for line in lines[1:]:
            line = line.strip()
            if line and "\tdevice" in line:
                device_id = line.split("\t")[0]
                logging.info(f"Found device: {device_id}")
                return device_id

        # No devices found
        raise RuntimeError(
            "No Android devices connected. Please connect a device and try again."
        )

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to execute 'adb devices': {e}")
    except FileNotFoundError:
        raise RuntimeError(
            "adb command not found. Please ensure Android SDK is installed and adb is in PATH."
        )


def main(appium_server_url, device):
    # Get the script's directory to build absolute paths
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Track overall success for class-level retry
    class_failed = False
    failed_therapy = None

    for item in device["therapy"]:
        driver = None
        try:
            # Handle both formats: "subdir/therapy" and "therapy"
            # Use forward slashes for cross-platform compatibility
            item_normalized = item.replace("\\", "/")
            config_path = os.path.join(script_dir, "configs", f"{item_normalized}.txt")
            # Ensure the path exists
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config file not found: {config_path}")

            with open(config_path, encoding="utf-8") as file:
                parsed, header = parser_beta_driver(file.read())

            logging.info(header)
            enable = True
            for key, val in header.items():
                if val == "True" or val == "False":
                    val = bool(val)
                    # print(val)
                # TODO add header exception
                if key == "popup":
                    enable = True if val == "True" else False
                elif key == "class":
                    continue
                else:
                    capabilities[key] = val

            # driver.quit()

            # ADD HERE

            try:
                device_udid = get_first_device_id()
            except RuntimeError as e:
                logging.error(f"Device error: {e}")
                return {
                    "success": False,
                    "failed_therapy": item,
                    "error": str(e),
                    "class": header.get("class", "None"),
                }
            capabilities["udid"] = device_udid
            print(capabilities)
            driver = webdriver.Remote(
                appium_server_url,
                options=UiAutomator2Options().load_capabilities(capabilities),
            )  # Driver initialization
            # driver.capabilities
            # Use popup-aware query processing
            process_queries_with_popup_handling(parsed, driver, item, enable)

        except Exception as e:
            print(f"Error processing therapy item {item}: {e}")
            class_failed = True
            failed_therapy = item

            # Try to handle any remaining popups before continuing
            if driver:
                popup_handler = PopupHandler(driver)
                popup_handler.dismiss_common_popups()
                popup_handler.handle_overlay_popups()

            # Re-raise to signal failure
            raise

        finally:
            if driver:
                try:
                    capabilities["noReset"] = False
                    driver.quit()
                    # logging.info("dummy")
                except Exception as e:
                    print(f"Error quitting driver: {e}")

    # Return success if no failures occurred
    return {"success": not class_failed, "failed_therapy": failed_therapy}


if __name__ == "__main__":
    # Your existing main execution code
    pass
