import logging
import time
import os
import shutil
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal # Switched to PyQt6
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, InvalidSessionIdException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import pythoncom

# Setup module logger
logger = logging.getLogger(__name__)

class BrowserController(QThread):
    """
    Handles browser automation for iHeartRadio.
    Now supports dynamic URLs.
    """
    status_update = pyqtSignal(str)

    def __init__(self, url="https://www.iheart.com/live/newsradio-830-khvh-4748/", browser_name="chrome"):
        super().__init__()
        self.url = url
        self.browser_name = (browser_name or "chrome").strip().lower()
        self.driver = None
        self.startup_error = None
        self.playback_confirmed = False
        self.play_click_attempted = False
        self.last_playback_status = "not-started"
        self.last_playback_confirmed_at = None
        self.keep_running = True
        self.setObjectName("BrowserThread")

    def _common_browser_args(self, options):
        options.add_argument("--autoplay-policy=no-user-gesture-required")
        options.add_argument("--disable-features=AudioServiceOutOfProcess")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-first-run-ui")
        options.add_argument("--disable-search-engine-choice-screen")
        # Anti-throttling flags to prevent silent stream crashes in background.
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        return options

    def _create_driver(self):
        if self.browser_name == "edge":
            edge_options = self._common_browser_args(EdgeOptions())
            edge_profile_dir = Path(os.environ.get(
                "IHEART_EDGE_PROFILE_DIR",
                Path.cwd() / ".edge-profile-iheart",
            ))
            edge_profile_dir.mkdir(parents=True, exist_ok=True)
            edge_options.add_argument(f"--user-data-dir={edge_profile_dir}")
            edge_options.add_argument("--profile-directory=Default")
            logging.info("Launching Microsoft Edge for browser automation.")
            driver_path = os.environ.get("IHEART_EDGE_DRIVER_PATH") or shutil.which("msedgedriver")
            if driver_path:
                logging.info("Using Edge WebDriver from %s", driver_path)
                return webdriver.Edge(service=EdgeService(driver_path), options=edge_options)
            try:
                # Prefer Selenium Manager for Edge. webdriver-manager 4.0.1 can
                # query an older msedgedriver.azureedge.net endpoint that fails
                # DNS on some systems even when normal browsing works.
                return webdriver.Edge(options=edge_options)
            except Exception as selenium_manager_err:
                logging.warning("Selenium Manager Edge startup failed: %s", selenium_manager_err)
                return webdriver.Edge(
                    service=EdgeService(EdgeChromiumDriverManager().install()),
                    options=edge_options,
                )

        if self.browser_name != "chrome":
            logging.warning("Unknown browser '%s'; falling back to Chrome.", self.browser_name)

        chrome_options = self._common_browser_args(ChromeOptions())
        logging.info("Launching Google Chrome for browser automation.")
        return webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options,
        )

    def stop(self):
        logging.info("Stop requested for browser thread.")
        self.keep_running = False
        if self.isRunning():
            self.wait(5000)
        if self.driver:
            try:
                self.driver.quit()
                logging.info("WebDriver quit successfully.")
            except Exception as e:
                logging.error(f"Error quitting WebDriver: {e}")
        if self.isRunning():
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
            self.startup_error = None
            self.driver = self._create_driver()
            
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

            # Make an immediate playback attempt before the steady keep-alive
            # loop so scheduled recordings do not start on a silent page.
            for _ in range(3):
                if not self.keep_running:
                    break
                self._handle_popups()
                if self._ensure_playing():
                    break
                time.sleep(2)
            
            # 2. Main Keep-Alive Loop (Continuously ensure playback)
            logging.info("Entering Keep-Alive Playback Loop...")
            
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
            self.startup_error = e
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

    def _confirm_playback(self, status):
        self.playback_confirmed = True
        self.last_playback_status = status
        self.last_playback_confirmed_at = time.time()

    def _find_play_buttons(self):
        """Find likely iHeart play controls across current UI variants."""
        selectors = [
            (By.CSS_SELECTOR, "button[data-test='play-button']"),
            (By.CSS_SELECTOR, "button[data-test*='play']"),
            (By.CSS_SELECTOR, "button[data-testid*='play']"),
            (By.CSS_SELECTOR, "button[aria-label*='Play']"),
            (By.CSS_SELECTOR, "button[title*='Play']"),
            (By.CSS_SELECTOR, "div[class*='Hero'] button"),
            (By.CSS_SELECTOR, "section button[aria-label*='Play']"),
            (By.CSS_SELECTOR, "[role='button'][aria-label*='Play']"),
            (
                By.XPATH,
                "//button[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'play') "
                "or contains(translate(@title, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'play') "
                "or contains(translate(@data-test, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'play') "
                "or contains(translate(@data-testid, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'play')]",
            ),
        ]
        buttons = []
        seen = set()
        for by, selector in selectors:
            try:
                for button in self.driver.find_elements(by, selector):
                    element_id = button.id
                    if element_id in seen:
                        continue
                    seen.add(element_id)
                    if button.is_displayed():
                        buttons.append(button)
            except Exception:
                continue
        return buttons

    def _nudge_media_elements(self):
        """Try HTML media playback directly when the visible button is not ready."""
        try:
            return self.driver.execute_script(
                """
                const media = Array.from(document.querySelectorAll('audio, video'));
                for (const el of media) {
                    try {
                        el.muted = false;
                        const result = el.play();
                        if (result && result.catch) result.catch(() => {});
                    } catch (err) {}
                }
                return media.some(el => el.readyState > 0 && !el.paused);
                """
            )
        except Exception as js_err:
            logging.debug("Media nudge failed: %s", js_err)
            return False

    def _ensure_playing(self):
        """Checks if the stream is playing; clicks play ONLY if it's not."""
        try:
            if self._nudge_media_elements():
                logging.debug("Playback already active in media element.")
                self.status_update.emit("Playback Active")
                self._confirm_playback("media-active")
                return True

            # 1. Find the play/stop button using multiple strategies.
            play_buttons = self._find_play_buttons()
            
            if not play_buttons:
                logging.info(
                    "No play button found on page yet. url=%s title=%s",
                    self.driver.current_url,
                    self.driver.title,
                )
                if self._nudge_media_elements():
                    logging.info("Playback confirmed by direct media element play().")
                    self.status_update.emit("Playback Active")
                    self._confirm_playback("media-element")
                    return True
                self.last_playback_status = "no-play-button"
                return False
            
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
                self._confirm_playback("button-state-playing")
                return True
            
            # Stream is NOT playing (IDLE, PAUSED, or unknown). Click to start.
            logging.info(f"Stream is NOT playing (state={data_state}, label={label}). Clicking Play...")
            self.status_update.emit("Clicking Play...")
            self.play_click_attempted = True
            self.last_playback_status = "clicking-play"
            
            try:
                # Scroll into view
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(0.5)
                
                # Click the button
                logging.info("Clicking play button candidate.")
                try:
                    btn.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", btn)
                
                # Wait for the stream to start (handles pre-roll ads)
                self.status_update.emit("Waiting for Stream/Ad...")
                start_wait = time.time()
                
                while self.keep_running and time.time() - start_wait < 60:
                    # Re-read state after click
                    try:
                        new_state = (btn.get_attribute("data-test-state") or "").strip().lower()
                        if new_state == "playing":
                            logging.info("Stream confirmed PLAYING after click.")
                            self.status_update.emit("Playback Active")
                            self._confirm_playback("confirmed-after-click")
                            return True
                    except Exception:
                        # Button may have been replaced in DOM after ad
                        logging.debug("Button reference lost (DOM changed). Assuming playback started.")
                        self.status_update.emit("Playback Active (assumed)")
                        self._confirm_playback("assumed-after-dom-change")
                        return True

                    if self._nudge_media_elements():
                        logging.info("Playback confirmed by media element after click.")
                        self.status_update.emit("Playback Active")
                        self._confirm_playback("media-after-click")
                        return True
                    
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
                self.last_playback_status = "playback-timeout"
                return False
                    
            except Exception as click_err:
                logging.error(f"Failed to click play button: {click_err}")
                self.last_playback_status = "play-click-failed"
                return False

        except Exception as e:
            logging.warning(f"Error in _ensure_playing: {e}")
            self.last_playback_status = "playback-check-error"
            return False
