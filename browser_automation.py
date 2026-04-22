import logging
import time
import os
from PyQt6.QtCore import QThread, pyqtSignal # Switched to PyQt6
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, InvalidSessionIdException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
import pythoncom

# Setup module logger
logger = logging.getLogger(__name__)

class BrowserController(QThread):
    """
    Handles browser automation for iHeartRadio.
    Now supports dynamic URLs.
    """
    status_update = pyqtSignal(str)

    def __init__(self, url="https://www.iheart.com/live/newsradio-830-khvh-4748/"):
        super().__init__()
        self.url = url
        self.driver = None
        self.keep_running = True
        self.setObjectName("BrowserThread")

    def stop(self):
        logging.info("Stop requested for browser thread.")
        self.keep_running = False
        if self.driver:
            try:
                self.driver.quit()
                logging.info("WebDriver quit successfully.")
            except Exception as e:
                logging.error(f"Error quitting WebDriver: {e}")
        self.wait()

    def run(self):
        logging.info("--- Browser Automation Thread Started ---")
        self.status_update.emit("Initializing Browser...")

        try:
            pythoncom.CoInitialize()
        except Exception as e:
            logging.error(f"Failed to init COM: {e}")
            return

        try:
            chrome_options = Options()
            chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
            chrome_options.add_argument("--disable-features=AudioServiceOutOfProcess")
            # Anti-throttling flags to prevent silent stream crashes in background
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            # chrome_options.add_argument("--headless") # Optional: make headless if requested
            
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            
            # Position window (optional)
            try:
                self.driver.set_window_position(0, 0)
                self.driver.set_window_size(1200, 800)
            except Exception:
                pass

            logging.info(f"Navigating to {self.url}...")
            self.status_update.emit(f"Navigating to Target: {self.url}")
            self.driver.get(self.url)
            
            # --- Page Interaction ---
            
            # 1. Wait for page load
            logging.info("Waiting for page load...")
            time.sleep(5) 
            
            # 2. Main Keep-Alive Loop (Continuously ensure playback)
            logging.info("Entering Keep-Alive Playback Loop...")
            no_play_btn_count = 0
            
            while self.keep_running:
                try:
                    # A. Setup/Popup Handling
                    self._handle_popups()
                    
                    # B. Ensure Playback
                    self._ensure_playing()
                except InvalidSessionIdException:
                    logging.error("WebDriver session is invalid. Breaking keep-alive loop.")
                    self.status_update.emit("Browser Session Lost")
                    break # Break the loop if session is lost
                except Exception as e:
                    logging.warning(f"Error in playback loop: {e}")
                    # If it's a general WebDriverException, it might be fatal
                    if isinstance(e, WebDriverException) and "session" in str(e).lower():
                        logging.error("Fatal WebDriver error detected. Breaking loop.")
                        break
                
                # Check every 5 seconds (more frequent to catch ads ending)
                for _ in range(5):
                    if not self.keep_running: break
                    time.sleep(1)
                
        except Exception as e:
            logging.error(f"Browser Automation Error: {e}", exc_info=True)
            self.status_update.emit(f"Error: {str(e)[:50]}")
        finally:
            if self.driver:
                self.driver.quit()
            pythoncom.CoUninitialize()
            
    def _handle_popups(self):
        """Dismisses common overlays/ads."""
        try:
            # Common selectors for "Close", "Dismiss", "No Thanks"
            # 1. Generic Modal Close buttons (often SVG or 'X')
            close_btns = self.driver.find_elements(By.CSS_SELECTOR, 'button[aria-label="Close"], button[aria-label="Dismiss"], [data-test="modal-close"]')
            
            # 2. Specific "Skip Ad" or "No Thanks" text
            if not close_btns:
                # Search by XPath for text content (slower but effective)
                close_btns = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'No Thanks') or contains(text(), 'Skip') or contains(text(), 'Dismiss')]")
            
            for btn in close_btns:
                try:
                    if btn.is_displayed():
                        logging.info("Popup/Ad detected. Closing...")
                        self.status_update.emit("Closing Popup...")
                        btn.click()
                        time.sleep(1) # Wait for animation
                except Exception:
                    pass
        except Exception as e:
             pass # Popups are transient, ignore errors

    def _ensure_playing(self):
        """Checks if the stream is playing; clicks play ONLY if it's not."""
        try:
            # 1. Find the play/stop button using multiple strategies
            # Strategy A: data-test attribute (most reliable for iHeart)
            play_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[data-test='play-button']")
            
            # Strategy B: Aria label containing "Play"
            if not play_buttons:
                play_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='Play']")
            
            # Strategy C: Hero section button
            if not play_buttons:
                play_buttons = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='Hero'] button, section button[aria-label*='Play']")
            
            if not play_buttons:
                logging.debug("No play button found on page. (May already be playing or page structure changed)")
                return
            
            btn = play_buttons[0]
            # Read the button's current state attributes
            label = (btn.get_attribute("aria-label") or "").strip()
            data_state = (btn.get_attribute("data-test-state") or "").strip()
            
            # --- CRITICAL FIX ---
            # iHeart uses data-test-state="PLAYING" (uppercase) when the stream is active
            # and data-test-state="IDLE" or "PAUSED" when stopped.
            # The aria-label is always "Play Button" regardless of state.
            # We must use CASE-INSENSITIVE comparison on data_state.
            
            state_lower = data_state.lower()
            
            if state_lower == "playing":
                # UI says it's playing, verify actual audio element is advancing
                try:
                    js = """
                    var media = document.querySelectorAll('audio, video');
                    for (var i = 0; i < media.length; i++) {
                        if (media[i].readyState > 0 && !media[i].paused) {
                            return media[i].currentTime;
                        }
                    }
                    return -1;
                    """
                    current_time = self.driver.execute_script(js)
                    
                    if current_time != -1:
                        last_time = getattr(self, '_last_media_time', -1)
                        if current_time == last_time:
                            self._stall_count = getattr(self, '_stall_count', 0) + 1
                            logging.debug(f"Stream stalled check: {self._stall_count}/6")
                            if self._stall_count >= 6:  # Approx 30s of infinite buffering
                                logging.warning("Stream is STALLED (currentTime frozen). Forcing page reload to recover.")
                                self.status_update.emit("Stream Stalled - Reloading...")
                                self.driver.refresh()
                                self._stall_count = 0
                                self._last_media_time = -1
                                time.sleep(5) # Wait for reload
                                return
                        else:
                            self._stall_count = 0  # Reset
                        self._last_media_time = current_time
                    else:
                        # UI says playing, but no media tag is active. Could be transitioning/loading.
                        self._stall_count = getattr(self, '_stall_count', 0) + 1
                        if self._stall_count >= 12: # Approx 60s
                            logging.warning("No active media tag found despite PLAYING state. Forcing reload.")
                            self.driver.refresh()
                            self._stall_count = 0
                            self._last_media_time = -1
                            time.sleep(5)
                            return

                except Exception as js_err:
                     logging.debug(f"Error checking JS stream time: {js_err}")

                logging.debug(f"Stream is PLAYING (state={data_state}). No action needed.")
                return
            
            # Stream is NOT playing (IDLE, PAUSED, or unknown). Click to start.
            logging.info(f"Stream is NOT playing (state={data_state}, label={label}). Clicking Play...")
            self.status_update.emit("Clicking Play...")
            
            try:
                # Scroll into view
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(0.5)
                
                # Click the button
                try:
                    btn.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", btn)
                
                # Wait for the stream to start (handles pre-roll ads)
                self.status_update.emit("Waiting for Stream/Ad...")
                start_wait = time.time()
                
                while time.time() - start_wait < 60:
                    # Re-read state after click
                    try:
                        new_state = (btn.get_attribute("data-test-state") or "").strip().lower()
                        if new_state == "playing":
                            logging.info("Stream confirmed PLAYING after click.")
                            self.status_update.emit("Playback Active")
                            return
                    except Exception:
                        # Button may have been replaced in DOM after ad
                        logging.debug("Button reference lost (DOM changed). Assuming playback started.")
                        self.status_update.emit("Playback Active (assumed)")
                        return
                    
                    # Check for ad modal overlay
                    try:
                        modals = self.driver.find_elements(By.CSS_SELECTOR, 'div[class*="modal"], section[role="dialog"]')
                        if modals and modals[0].is_displayed():
                            logging.info("Ad overlay detected. Waiting for it to finish...")
                            time.sleep(2)
                            continue
                    except Exception:
                        pass
                    
                    time.sleep(1)
                
                logging.warning("Timed out waiting for stream to start after clicking Play.")
                self.status_update.emit("Playback Timeout - will retry")
                    
            except Exception as click_err:
                logging.error(f"Failed to click play button: {click_err}")

        except Exception as e:
            logging.warning(f"Error in _ensure_playing: {e}")
