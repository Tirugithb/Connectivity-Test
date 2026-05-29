import json
import logging
from ssl import Options
import re


class Args:
    """Holds CLI arguments as a key-value store with typed getters and setters."""

    def __init__(self):
        self._store: dict = {}

    # --- generic key/value interface ---

    def set(self, key: str, value) -> None:
        """Store any key-value pair (key stored lowercase)."""
        self._store[key.lower()] = value

    def get(self, key: str, default=None):
        """Retrieve a value by key (case-insensitive)."""
        return self._store.get(key.lower(), default)

    def all(self) -> dict:
        """Return a copy of the full key-value store."""
        return dict(self._store)

    def substitute(self, text: str) -> str:
        """Replace {KEY} placeholders in *text* with stored values."""
        for key, value in self._store.items():
            text = text.replace(f"{{{key.upper()}}}", str(value))
        return text

    # --- named property shortcuts ---

    @property
    def device(self) -> str:
        return self._store.get("device", "")

    @device.setter
    def device(self, value: str) -> None:
        self._store["device"] = value

    def __repr__(self) -> str:
        return f"Args({self._store})"


# Module-level singleton used by parse_query / get_args
_args = Args()


def get_runtime_args() -> Args:
    """Return the module-level Args singleton."""
    return _args


"""
@ Button
& Switch
* Radio Button
& Switch
_text_ Add text
v Chevron
V Chevron with right offset
() Dropdown selection
  Text 
-} Drag and drop
"" Add text
// comments the query
+ Linear layout
area Electrode placement
ham Hamburger symbol
setting
display_icon
_ss_ screenshot
"""

"""
Enhanced parser with if/else functionality

New syntax additions:
if(condition) then statement1 > statement2 else statement3 > statement4
if(check_text_exists) then @button1 else @button2
if(element_visible) then setting2 > Rate else @skip

Conditions supported:
- check(text) - checks if text exists on screen
- element(xpath) - checks if element exists
- visible(text) - checks if element is visible
- enabled(text) - checks if element is enabled
"""


def optional_fn(query: str):
    if query.endswith("*"):
        return query[:-1], True
    return query, False


def parse_condition(condition_str):
    """Parse condition string and return condition details"""
    condition_str = condition_str.strip()

    # Handle different condition types
    if condition_str.startswith("check(") and condition_str.endswith(")"):
        text = condition_str[6:-1]
        return {"type": "check_text", "text": text}
    elif condition_str.startswith("element(") and condition_str.endswith(")"):
        xpath = condition_str[8:-1]
        return {"type": "element_exists", "xpath": xpath}
    elif condition_str.startswith("visible(") and condition_str.endswith(")"):
        text = condition_str[8:-1]
        return {"type": "element_visible", "text": text}
    # elif condition_str.startswith("enabled(") and condition_str.endswith(")"):
    #     text = condition_str[8:-1]
    #     return {"type": "element_enabled", "text": text}
    else:
        # Default to text check for backward compatibility
        return {"type": "check_text", "text": condition_str}


def parse_if_else_statement(query):
    """Parse if/else statements"""
    # Pattern: if(condition) then statements else statements
    if_pattern = r"if\s*\(([^)]+)\)\s+then\s+(.+?)(?:\s+else\s+(.+))?$"
    match = re.search(if_pattern, query, re.IGNORECASE)

    if not match:
        return None

    condition_str = match.group(1)
    then_statements = match.group(2)
    else_statements = match.group(3) if match.group(3) else ""

    # Parse condition
    condition = parse_condition(condition_str)

    # Parse then statements (split by >)
    then_steps = []
    if then_statements:
        for step in then_statements.split(">"):
            step = step.strip()
            if step:
                then_steps.append(parse_query(step, 0))

    # Parse else statements (split by >)
    else_steps = []
    if else_statements:
        for step in else_statements.split(">"):
            step = step.strip()
            if step:
                else_steps.append(parse_query(step, 0))

    return {
        "type": "conditional",
        "condition": condition,
        "then_steps": then_steps,
        "else_steps": else_steps,
        "optional": False,
        "time": 10,
    }


def get_args(query: str) -> str:
    """Substitute {KEY} placeholders in *query* using the current Args store."""
    return _args.get(query)
    # return _args.substitute(query)


def parse_query(query, flag):
    parsed_result = {}

    # Check for if/else statements first
    if_else_result = parse_if_else_statement(query)
    if if_else_result:
        return if_else_result

    if query.endswith("*") or flag == 1:  # Checking for optional query
        parsed_result["optional"] = True
        if query.endswith("*"):
            query = query[:-1]
    else:
        parsed_result["optional"] = False

    default_time = 10  # DEFAULT TIMEOUT FOR QUERIES
    temp = [t.strip() for t in query.split("::")]  # Explicit timeout using ::
    query = temp[0]

    try:
        delta = temp[1] if len(temp) > 1 else default_time
    except IndexError:
        delta = default_time

    parsed_result["time"] = delta

    if query.startswith("*"):  # Radio Button
        arr = [t.strip() for t in query[1:].split("|")]
        text = arr[1] if len(arr) > 1 else query[1:]
        parsed_result["type"] = "radio_button"
        parsed_result["resource_id"] = arr[0].lower() if len(arr) > 1 else None
        parsed_result["text"] = get_args(text[2:]) if text.startswith("--") else text

    elif query == "_noti_":  # Notification panel
        parsed_result["type"] = "noti"

    elif query == "_back_":  # Press back button
        parsed_result["type"] = "back"

    elif query.startswith("script(") and query.endswith(")"):  # Executing shell command
        text = query[7:-1]
        parsed_result["type"] = "script"
        parsed_result["text"] = text
    elif query.startswith("exec(") and query.endswith(")"):  # Executing shell command
        text = query[5:-1]
        parsed_result["type"] = "exec"
        parsed_result["text"] = text

    elif query.startswith("checkbox(") and query.endswith(")"):
        text = query[9:-1]
        parsed_result["type"] = "checkbox"
        parsed_result["text"] = text

    elif query.startswith("swipe(") and query.endswith(")"):
        text = query[6:-1]
        parsed_result["type"] = "swipe"
        parsed_result["text"] = text

    elif query.startswith("xpath(") and query.endswith(")"):
        text = query[6:-1]
        parsed_result["type"] = "xpath"
        parsed_result["text"] = text

    elif query.startswith("delay(") and query.endswith(")"):
        text = query[6:-1]
        parsed_result["type"] = "delay"
        parsed_result["text"] = float(text)

    elif query.startswith("delta(") and query.endswith(")"):  # Delta timestamp
        text = query[6:-1]
        parsed_result["type"] = "delta"
        parsed_result["text"] = text

    elif query.startswith("id(") and query.endswith(")"):  # element id
        text = query[3:-1]
        parsed_result["type"] = "id"
        parsed_result["text"] = text

    elif query.startswith("res-id(") and query.endswith(")"):  # resource id
        text = query[7:-1]
        parsed_result["type"] = "resid"
        parsed_result["text"] = text

    # TODO key val
    elif query.startswith("keyval(") and query.endswith(")"):
        text = query[7:-1]
        parsed_result["type"] = "keyval"
        parsed_result["text"] = text

    elif query.startswith("@"):  # Button
        text = query[1:]
        parsed_result["type"] = "button"
        parsed_result["text"] = text

    elif query.startswith("v"):  # Chevron
        text = query[1:]
        parsed_result["type"] = "chevron"
        parsed_result["text"] = text

    elif query.startswith("V"):  # Chevron with right offset
        text = query[1:]
        parsed_result["type"] = "chevron_offset"
        parsed_result["text"] = text

    elif query.startswith("(") and query.endswith(")"):  # Dropdown Selection
        text = query[1:-1]
        parsed_result["type"] = "dropdown"
        parsed_result["text"] = text

    elif query.startswith("+"):  # Linear Layout
        text = query[1:]
        parsed_result["type"] = "linear_layout"
        parsed_result["content_desc"] = text

    elif "_text_" in query:  # Add text
        arr = [t for t in query.split("_text_")]
        text = arr[1]
        parsed_result["type"] = "add_text"
        # parsed_result["text"] = arr[0].replace(" ", "").lower()
        parsed_result["text"] = arr[0]
        parsed_result["input"] = text

    elif query.startswith("area"):  # Electrode Placement
        text = query[4:]
        parsed_result["type"] = "electrode_placement"
        parsed_result["index"] = text

    elif query.startswith("h&"):  # Switch
        # arr = [t.strip() for t in query.split("||")]
        text = query[2:]
        # enable = arr[1] == "on"
        # parsed_result["enable"] = enable
        parsed_result["type"] = "h_toggle"
        parsed_result["text"] = text
    elif query.startswith("&"):  # Switch
        arr = [t.strip() for t in query.split("||")]
        text = arr[0][1:]
        enable = arr[1] == "on"
        parsed_result["enable"] = enable
        parsed_result["type"] = "switch"
        parsed_result["text"] = text

    elif "-}" in query:  # Drag and Drop
        arr = [t.strip() for t in query.split("-}")]
        parsed_result["type"] = "drag_drop"
        parsed_result["source"] = arr[0]
        parsed_result["destination"] = arr[1]

    elif "_next_" == query:  # Right Chevron
        parsed_result["type"] = "next"

    elif query.startswith("qs_"):  # quick setting
        arr = [t.strip() for t in query[3:].split(":")]
        parsed_result["type"] = "qs"
        parsed_result["text"] = arr[0]
        parsed_result["enable"] = True if arr[1] == "on" else False

    elif "fw_btn" == query:  # fw btn
        parsed_result["type"] = "fw"

    elif "bk_btn" == query:  # bk btn
        parsed_result["type"] = "bk"

    elif "up_arrow" == query:  # Up symbol
        parsed_result["type"] = "up"

    elif "down_arrow" == query:  # Down symbol
        parsed_result["type"] = "down"

    elif "prev_track" == query:
        parsed_result["type"] = "prev_track"

    elif "next_track" == query:
        parsed_result["type"] = "next_track"

    elif "ham" == query:  # Hamburger symbol
        parsed_result["type"] = "hamburger"

    elif "setting2" == query:  # Setting2
        parsed_result["type"] = "setting2"

    elif "setting" == query:  # Setting2
        parsed_result["type"] = "setting"

    elif "display_icon" == query:
        parsed_result["type"] = "display_icon"

    elif query.startswith("_ss_"):  # Screenshot
        text = query[4:]
        parsed_result["type"] = "screenshot"
        parsed_result["text"] = text

    elif query.startswith("check_raw(") and query.endswith(
        ")"
    ):  # check for raw and screenshot
        text = query
        parsed_result["type"] = "check_raw"
        parsed_result["text"] = query[10:-1]
    elif query.startswith("tap(") and query.endswith(")"):  # tap
        # text = query
        # arr = [t.strip() for t in query[4:].split(",")]
        parsed_result["type"] = "tap"
        parsed_result["text"] = query[4:-1]

    elif query.startswith("check-id(") and query.endswith(")"):  # check
        text = query
        parsed_result["type"] = "checkid"
        parsed_result["text"] = query[9:-1]

    elif query.startswith("check(") and query.endswith(")"):  # check
        text = query
        parsed_result["type"] = "check"
        parsed_result["text"] = query[6:-1]

    elif query.startswith("scroll(") and query.endswith(")"):
        text = query[7:-1]
        parsed_result["type"] = "scroll"
        parsed_result["text"] = text

    elif query.startswith("print(") and query.endswith(")"):
        text = query[6:-1]
        parsed_result["type"] = "print"
        parsed_result["text"] = text
    # elif query.startswith("scroll_up(") and query.endswith(")"):
    #     text = query[12:-1]
    #     parsed_result["type"] = "scroll_up"
    #     parsed_result["text"] = text

    # elif query.startswith("scroll_down(") and query.endswith(")"):
    #     text = query[12:-1]
    #     parsed_result["type"] = "scroll_down"
    #     parsed_result["text"] = text

    else:  # Default Case
        parsed_result["type"] = "text_view"
        parsed_result["text"] = query

    return parsed_result


def parse_query_line(line):
    line = line.strip()
    if line.startswith("//"):  # Handle comments
        return None  # Skip comments

    name, steps = line.split("=", 1)
    name = name.strip()

    flag = 0
    if name.endswith("*"):  # Check if entire query is optional
        flag = 1

    steps = [step.strip() for step in steps.split(">")]

    parsed_steps = []
    for step in steps:
        parsed_steps.append(
            parse_query(step, flag)
        )  # Use the previously defined parse_query function

    return {"name": name, "steps": parsed_steps}


def parse_all_queries(input_text):
    parsed_queries = []
    header = {}
    for line in input_text.split("\n"):
        if line == "":
            continue
        if line.startswith("###"):  # appium declaration
            arr = line.split(" ")
            header[arr[1]] = arr[2]
        else:
            parsed_line = parse_query_line(line)
            if parsed_line:
                parsed_queries.append(parsed_line)
    return parsed_queries, header


# Parse the input queries
def parser_beta_driver(query_text: str) -> list:
    parsed_output, flag = parse_all_queries(query_text)  # Parsing driver code
    return parsed_output, flag
