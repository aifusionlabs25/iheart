import time

from browser_automation import BrowserController


def test_edge_launch_url():
    url = "https://www.iheart.com/live/newsradio-830-khvh-4748/"
    browser = BrowserController(url, browser_name="edge")
    browser.start()
    print("Edge launch test started. Waiting 20 seconds...")
    time.sleep(20)
    browser.stop()
    print("Edge launch test complete.")


if __name__ == "__main__":
    test_edge_launch_url()
