from browser_automation import BrowserController


def test_browser_controller_defaults_to_chrome():
    browser = BrowserController("https://example.com")
    assert browser.browser_name == "chrome"


def test_browser_controller_accepts_edge():
    browser = BrowserController("https://example.com", browser_name="edge")
    assert browser.browser_name == "edge"
