# Literal tapping on screen using x, y coordinate
def tap(x: int, y: int, driver):
    driver.tap([(x, y)])
