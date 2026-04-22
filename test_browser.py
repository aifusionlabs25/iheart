from browser_automation import BrowserController
import time
import logging

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

def test_browser():
    print("--- Testing Browser Automation ---")
    url = "https://www.iheart.com/live/newsradio-830-khvh-4748/"
    print(f"Target URL: {url}")
    
    try:
        browser = BrowserController(url)
        browser.start()
        
        print("Browser thread started. Waiting 30 seconds to observe...")
        time.sleep(30)
        
        print("Stopping browser...")
        browser.stop()
        print("Test complete.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_browser()
