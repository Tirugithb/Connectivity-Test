from datetime import datetime
import argparse
import logging
import random
import threading
import time
from queue import Queue
import sys
import os
import re
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

# Import required application modules
# from app import main
from popup import main
from scripts.run_apps import run
import shutil
from src.parser_beta import get_runtime_args

# Mapping of device serial numbers to config folder names in configs bak
DEVICE_CONFIG_MAP: Dict[str, str] = {
    "NPI705951H": "7_DBS_PC",
    "NND500395H": "8_DBS_RC",
    "NMS505519H": "3_Vanta",
    "NNC500298H": "5_Inceptiv",
    "NME741732H": "9_Intellis",
    "NMB709025": "4_Restore",
    "NLJ387366N": "10_Trailing",
    "NGP005083H": "1_SM2",
    "NFY001793H": "2_SM3",
    "NTI501973H": "11_Altaviva",
}
CONFIGS_BAK_SUBDIR = "Tablet_a4p"


class ConnectionPool:
    """Manages a pool of Docker connection ports with thread-safe access"""

    def __init__(self, ports: List[int] = None, wait_timeout: int = 60):
        """Initialize the connection pool

        Args:
            ports: List of available Docker ports (defaults to [4723, 4724, 4725])
            wait_timeout: Maximum wait time for connection in seconds
        """
        self.available_ports = ports or [4723, 4724, 4725]
        self.in_use_ports = set()
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.wait_timeout = wait_timeout
        self.logger = logging.getLogger("ConnectionPool")

    def get_connection(self, delay: float = 0.5) -> Optional[int]:
        """Get an available connection port from the pool

        Args:
            delay: Delay in seconds to reduce race conditions (default: 0.5)

        Returns:
            Port number if available, None if timeout occurs
        """
        start_time = time.time()
        with self.condition:
            while not self.available_ports:
                remaining = self.wait_timeout - (time.time() - start_time)
                if remaining <= 0:
                    self.logger.error("Timeout waiting for available connection")
                    sys.exit(2)  # skip
                    return None

                self.logger.debug(
                    f"Waiting for available connection (timeout in {remaining:.1f}s)"
                )
                self.condition.wait(
                    min(remaining, 5)
                )  # Wait at most 5 seconds at a time

            # Get a port and mark it as in-use
            port = self.available_ports.pop(0)
            self.in_use_ports.add(port)

            # Add a small delay to reduce race conditions
            if delay > 0:
                time.sleep(delay)

            self.logger.debug(f"Allocated port: {port}")
            return port

    def release_connection(self, port: int) -> None:
        """Release a connection port back to the pool

        Args:
            port: The port number to release
        """
        with self.condition:
            if port in self.in_use_ports:
                self.in_use_ports.remove(port)
                self.available_ports.append(port)
                self.logger.debug(f"Released port: {port}")
                self.condition.notify()
            else:
                self.logger.warning(f"Attempted to release unallocated port: {port}")

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the connection pool

        Returns:
            Dictionary with available and in-use ports
        """
        with self.lock:
            return {
                "available": self.available_ports.copy(),
                "in_use": list(self.in_use_ports),
                "total": len(self.available_ports) + len(self.in_use_ports),
            }


class TaskExecutor:
    """Enhanced thread queue for executing tasks with connection pooling"""

    def __init__(
        self,
        pool: ConnectionPool,
        devices: List[Dict[str, List[str]]],
        max_retries: int = 2,
        retry_delay: int = 3,
    ):
        """Initialize the task executor

        Args:
            pool: Connection pool to use
            devices: List of device configurations
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.pool = pool
        self.devices = devices
        self.processed_devices = None  # Will be set in run_all()
        self.queue = Queue()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.results = {}
        self.lock = threading.Lock()
        self.logger = logging.getLogger("TaskExecutor")

    def process_task(self, device_index: int) -> bool:
        """Process a single device task with retry capability

        Args:
            device_index: Index of the device in the expanded devices list

        Returns:
            True if processing was successful, False otherwise
        """
        # Use the processed devices list instead of the original
        if self.processed_devices is None:
            self.logger.error("Processed devices list not initialized")
            sys.exit(1)  # fail
            return False

        if device_index >= len(self.processed_devices):
            self.logger.error(
                f"Device index {device_index} out of range for processed devices"
            )
            sys.exit(1)  # fail
            return False

        device = self.processed_devices[device_index]
        thread_name = threading.current_thread().name
        success = False

        for attempt in range(1, self.max_retries + 1):
            port = self.pool.get_connection(delay=1.0 if attempt > 1 else 0.5)
            if port is None:
                self.logger.error(
                    f"{thread_name}: Failed to get connection for device {device}"
                )
                sys.exit(2)  # skip
                return False

            try:
                self.logger.info(
                    f"{thread_name}: Using connection: {port} (Attempt {attempt}/{self.max_retries})"
                )

                # Run the task with the allocated port
                server_url = f"http://127.0.0.1:{port}"
                main(server_url, device)  # Call to app.py's main function

                # Task completed successfully
                success = True
                with self.lock:
                    self.results[device_index] = {
                        "success": True,
                        "attempts": attempt,
                        "port": port,
                        "device": device,  # Store the actual device config for reference
                    }

                self.logger.info(
                    f"{thread_name}: Successfully processed device: {device}"
                )
                break

            except Exception as e:
                error_msg = str(e)
                self.logger.error(
                    f"{thread_name}: Error processing device: {error_msg}"
                )

                with self.lock:
                    self.results[device_index] = {
                        "success": False,
                        "attempts": attempt,
                        "error": error_msg,
                        "device": device,  # Store the actual device config for reference
                    }

                # Only retry if we have attempts left
                if attempt < self.max_retries:
                    self.logger.info(
                        f"{thread_name}: Will retry in {self.retry_delay} seconds"
                    )
                    time.sleep(self.retry_delay)
            finally:
                self.logger.info(f"{thread_name}: Releasing connection: {port}")
                self.pool.release_connection(port)

        return success

    def process_queue(self) -> None:
        """Process tasks from the queue until empty"""
        while not self.queue.empty():
            try:
                device_index = self.queue.get(block=False)
                self.process_task(device_index)
            except Exception as e:
                self.logger.error(f"Unexpected error in queue processing: {str(e)}")
                sys.exit(1)  # fail
            finally:
                self.queue.task_done()

    def expand_device_list(self) -> List[Dict[str, List[str]]]:
        """Process device list - keeps devices with multiple therapies as single devices

        Note: This method now preserves devices with multiple therapies as single devices
        that will run all therapies sequentially, rather than expanding them into separate devices.

        Returns:
            List of devices (no expansion, just validation)
        """
        processed_devices = []

        for device in self.devices:
            # Keep the original device configuration as-is
            # A device with multiple therapies will run them sequentially
            processed_devices.append(device.copy())

        return processed_devices

    def run_all(self, use_thread_pool: bool = True) -> Dict[int, Dict[str, Any]]:
        """Run all devices with optimal threading

        Args:
            use_thread_pool: Whether to use ThreadPoolExecutor instead of raw threads

        Returns:
            Dictionary with results for each device
        """
        # Process devices (no expansion, just validation)
        self.processed_devices = self.expand_device_list()
        num_devices = len(self.processed_devices)
        self.results = {}

        # Determine optimal number of worker threads
        max_workers = min(
            num_devices, len(self.pool.available_ports) + len(self.pool.in_use_ports)
        )

        self.logger.info(f"Original devices: {len(self.devices)}")
        self.logger.info(f"Processing {num_devices} devices (no expansion)")
        self.logger.info(f"Device configs: {self.processed_devices}")
        self.logger.info(
            f"Starting execution with {num_devices} devices using {max_workers} worker threads"
        )

        if use_thread_pool:
            # Using ThreadPoolExecutor for better thread management
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for i in range(num_devices):
                    futures.append(executor.submit(self.process_task, i))

                # Wait for all futures to complete
                for i, future in enumerate(futures):
                    try:
                        result = future.result()
                        if i not in self.results:
                            self.results[i] = {"success": result, "attempts": 1}
                    except Exception as e:
                        self.logger.error(f"Error in thread pool future {i}: {str(e)}")
                        sys.exit(1)  # fail
                        if i not in self.results:
                            self.results[i] = {"success": False, "error": str(e)}
        else:
            # Using traditional threading approach
            for i in range(num_devices):
                self.queue.put(i)

            threads = []
            for i in range(max_workers):
                thread = threading.Thread(
                    target=self.process_queue, name=f"Worker-{i+1}"
                )
                thread.daemon = True
                threads.append(thread)
                thread.start()

            # Wait for the queue to be fully processed
            self.queue.join()

        return self.results


def load_configs_from_directory(
    config_dir: str = None,
) -> List[Dict[str, List[str]]]:
    """Load config files from directory and subdirectories, organizing them based on numeric patterns

    This function supports two modes:
    1. If subdirectories exist in config_dir, it reads each subdirectory as a separate schedule
    2. If no subdirectories exist, it reads all config files from the main directory

    Args:
        config_dir: Path to the configs directory (defaults to 'configs' relative to script location)

    Returns:
        List of device configurations grouped by numeric patterns
    """
    logger = logging.getLogger("ConfigLoader")

    # Resolve default config directory relative to script location
    if config_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(script_dir, "configs")

    # if not os.path.isdir(config_dir):
    if not os.path.exists(config_dir):
        logger.error(f"Config directory not found: {config_dir}")
        sys.exit(1)  # fail
        return []

    # Check for subdirectories (excluding __pycache__ and bak)
    subdirs = []
    for item in os.listdir(config_dir):
        item_path = os.path.join(config_dir, item)
        if os.path.isdir(item_path) and item not in ["__pycache__", "bak"]:
            subdirs.append(item)

    # If subdirectories exist, use them for scheduling
    if subdirs:
        logger.info(f"Found {len(subdirs)} subdirectories for scheduling: {subdirs}")
        # Group subdirectories by numeric prefix
        prefix_groups = {}
        for subdir in subdirs:
            number_match = re.match(r"^(\d+)", subdir)
            if number_match:
                prefix = int(number_match.group(1))
                if prefix not in prefix_groups:
                    prefix_groups[prefix] = []
                prefix_groups[prefix].append(subdir)
            else:
                # Non-numeric subdirs go to the end with a special key
                if "no_prefix" not in prefix_groups:
                    prefix_groups["no_prefix"] = []
                prefix_groups["no_prefix"].append(subdir)

        # Sort prefix groups and create devices based on prefix type
        all_devices = []
        all_sequential_therapies = []
        sorted_prefixes = sorted([k for k in prefix_groups.keys() if k != "no_prefix"])

        # Process all numbered prefixes sequentially (combine into single device)
        for prefix in sorted_prefixes:
            subdirs_in_group = prefix_groups[prefix]

            for subdir in sorted(subdirs_in_group):
                subdir_path = os.path.join(config_dir, subdir)
                logger.info(
                    f"Processing schedule directory: {subdir} (prefix: {prefix} - sequential)"
                )
                therapies = _load_therapies_from_path(subdir_path, subdir, logger)

                if therapies:
                    logger.info(
                        f"Adding {len(therapies)} therapies from {subdir} to sequential execution"
                    )
                    all_sequential_therapies.extend(therapies)

        # Create a single device for all therapies with numeric prefixes
        if all_sequential_therapies:
            logger.info(
                f"Creating single sequential device with {len(all_sequential_therapies)} total therapies from all numbered subdirectories"
            )
            all_devices.append({"therapy": all_sequential_therapies})

        # Process subdirectories without prefix - each becomes a parallel device
        if "no_prefix" in prefix_groups:
            logger.info(f"Creating parallel devices for subdirectories without prefix")
            for subdir in sorted(prefix_groups["no_prefix"]):
                subdir_path = os.path.join(config_dir, subdir)
                logger.info(
                    f"Processing schedule directory: {subdir} (no prefix - parallel)"
                )
                therapies = _load_therapies_from_path(subdir_path, subdir, logger)

                if therapies:
                    logger.info(
                        f"Creating parallel device for {subdir} with {len(therapies)} therapies"
                    )
                    all_devices.append({"therapy": therapies})

        return all_devices
    else:
        # No subdirectories, process the main directory
        logger.info("No subdirectories found, processing main configs directory")
        therapies = _load_therapies_from_path(config_dir, "", logger)
        if therapies:
            return [{"therapy": therapies}]
        return []


def _load_therapies_from_path(path: str, subdir: str, logger) -> List[str]:
    """Helper function to recursively load therapy names from config files and subdirectories

    Args:
        path: Path to search for config files and subdirectories
        subdir: Subdirectory name (or empty string if in main configs)
        logger: Logger instance

    Returns:
        List of therapy paths (relative to configs/) sorted by numeric prefix
    """
    all_items = []

    # Collect both files and subdirectories
    for item in os.listdir(path):
        item_path = os.path.join(path, item)

        if os.path.isfile(item_path) and item.endswith(".txt"):
            # It's a config file
            therapy_name = item.replace("config", "").replace(".txt", "")
            prefix_match = re.match(r"^(\d+)", therapy_name)

            if prefix_match:
                prefix_number = int(prefix_match.group(1))
                all_items.append((prefix_number, "file", therapy_name, None))
            else:
                all_items.append((float("inf"), "file", therapy_name, None))

        elif os.path.isdir(item_path) and item not in ["__pycache__", "bak"]:
            # It's a subdirectory - add it to be processed recursively
            prefix_match = re.match(r"^(\d+)", item)

            if prefix_match:
                prefix_number = int(prefix_match.group(1))
                all_items.append((prefix_number, "dir", item, item_path))
            else:
                all_items.append((float("inf"), "dir", item, item_path))

    # Sort all items by numeric prefix
    all_items.sort(key=lambda x: x[0])

    # Process items in order
    sorted_therapies = []
    for prefix, item_type, name, item_path in all_items:
        if item_type == "file":
            # Build relative path for file
            if subdir:
                therapy_path = f"{subdir}/{name}"
            else:
                therapy_path = name
            logger.info(f"Adding therapy: {therapy_path}")
            sorted_therapies.append(therapy_path)

        elif item_type == "dir":
            # Recursively process subdirectory
            nested_subdir = f"{subdir}/{name}" if subdir else name
            logger.info(f"Recursively processing subdirectory: {nested_subdir}")
            nested_therapies = _load_therapies_from_path(
                item_path, nested_subdir, logger
            )
            sorted_therapies.extend(nested_therapies)

    return sorted_therapies


def main_handler():
    """Main entry point with enhanced error handling and logging"""
    # Create logs directory if it doesn't exist
    os.makedirs("C:/Users/SVC-Systems-TestPC/Log_Screenshot_files/logs", exist_ok=True)
    # os.makedirs("./Log_Screenshot_files/logs", exist_ok=True)

    # Set up logging
    log_format = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            # logging.FileHandler(
            #     f"./logs/debug_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
            # ),
            logging.FileHandler(
                rf"C:/Users/SVC-Systems-TestPC/Log_Screenshot_files/logs/debug_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
            ),
            logging.StreamHandler(sys.stdout),
        ],
    )

    logger = logging.getLogger("main")
    logger.info("Starting application execution")

    # Record start time for performance measurement
    start_time = time.perf_counter()

    # Initialize connection pool
    pool = ConnectionPool(ports=[4723, 4724, 4725], wait_timeout=120)

    # Resolve config directory from device SN mapping
    args = get_runtime_args()
    device_sn = args.device
    config_dir = None
    if device_sn and device_sn in DEVICE_CONFIG_MAP:
        folder_name = DEVICE_CONFIG_MAP[device_sn]
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(
            script_dir, "configs bak", CONFIGS_BAK_SUBDIR, folder_name
        )
        logger.info(
            f"Device {device_sn} -> loading config folder: {folder_name} ({config_dir})"
        )
    elif device_sn:
        logger.warning(
            f"Device SN '{device_sn}' not found in DEVICE_CONFIG_MAP, falling back to default configs/"
        )

    # Store resolved config_dir in Args so popup.py can use it
    script_dir_main = os.path.dirname(os.path.abspath(__file__))
    args.set(
        "config_dir",
        config_dir if config_dir else os.path.join(script_dir_main, "configs"),
    )

    # Load devices from config directory
    # This will read all config files and group them based on numeric patterns in filenames
    devices = load_configs_from_directory(config_dir)

    # If you want to manually override or add specific devices, uncomment and modify below:
    # devices = [
    #     {"therapy": ["PHCP", "PHPP"]},
    #     {"therapy": ["VANTAPP", "ENROLLA10E", "ISII_3", "ISII_4"]},
    # ]

    if not devices:
        logger.error("No devices loaded. Exiting.")
        sys.exit(1)  # fail
        return

    try:
        # Create and run the task executor
        executor = TaskExecutor(pool, devices, max_retries=2, retry_delay=3)
        results = executor.run_all(use_thread_pool=True)

        # Calculate success rate using the processed device count
        success_count = sum(1 for r in results.values() if r.get("success", False))
        processed_count = len(executor.processed_devices)

        # Print summary
        logger.info("=== Execution Summary ===")
        logger.info(
            f"Success rate: {success_count}/{processed_count} ({(success_count/processed_count)*100:.1f}%)"
        )

        # Print failures if any
        failures = [(i, r) for i, r in results.items() if not r.get("success", False)]
        if failures:
            logger.info(f"Failed executions ({len(failures)}):")
            for idx, result in failures:
                error = result.get("error", "Unknown error")
                attempts = result.get("attempts", 0)
                device_config = result.get("device", "Unknown device")
                logger.info(
                    f"  Device {idx} ({device_config}): Failed after {attempts} attempts - {error}"
                )

        # Print successful executions
        successes = [(i, r) for i, r in results.items() if r.get("success", False)]
        if successes:
            logger.info(f"Successful executions ({len(successes)}):")
            for idx, result in successes:
                attempts = result.get("attempts", 0)
                device_config = result.get("device", "Unknown device")
                port = result.get("port", "Unknown port")
                logger.info(
                    f"  Device {idx} ({device_config}): Success after {attempts} attempts on port {port}"
                )

    except KeyboardInterrupt:
        logger.info("Execution interrupted by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        sys.exit(1)  # fail
    finally:
        # Calculate and log total execution time
        execution_time = time.perf_counter() - start_time
        logger.info(f"Total execution time: {execution_time:.2f} seconds")


def get_args():
    """Parse CLI arguments and populate the shared Args instance."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", required=True, help="Device serial number (INS)")
    # Add more arguments here and they are automatically available as {KEY} placeholders
    known, unknown = parser.parse_known_args()

    args = get_runtime_args()
    for key, value in vars(known).items():
        args.set(key, value)
    # Also store any extra --key=value pairs passed at runtime
    i = 0
    while i < len(unknown):
        token = unknown[i]
        if token.startswith("--"):
            token = token.lstrip("-")
            if "=" in token:
                k, v = token.split("=", 1)
                args.set(k, v)
            elif i + 1 < len(unknown) and not unknown[i + 1].startswith("--"):
                args.set(token, unknown[i + 1])
                i += 1
        i += 1

    print(f"[INFO] Running Connectivity Test on device: {args.device}")
    return args


if __name__ == "__main__":
    # log_dir = r"./Log_Screenshot_files"
    get_args()
    log_dir = r"C:/Users/SVC-Systems-TestPC/Log_Screenshot_files"
    # if os.path.exists(log_dir):
    #     shutil.rmtree(log_dir)
    os.makedirs(log_dir, exist_ok=True)
    main_handler()
