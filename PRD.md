# Product Requirements Document (PRD): iHeart Radio Recorder

## 1. Product Overview
**Product Name:** iHeart Radio Recorder  
**Purpose:** An automated desktop application designed to record live audio streams from iHeartRadio without user intervention. It handles browser navigation, playback initiation (including ad/popup management), audio capture via system audio (Stereo Mix/WASAPI), and file processing.

**Key Value Proposition:**
- **Reliability:** Uses a dedicated "Direct Mission" script (`run_mission.py`) optimized for Windows Task Scheduler to wake the PC and record unattended.
- **Resilience:** Monitors playback state in real-time to recover from stream interruptions or ads.
- **Automation:** Handles pre-roll ads and dynamic "Play" button states automatically.
- **Efficiency:** Compresses recordings to optimized MP3s and manages local file retention.

---

## 2. Core Features

### 2.1 Automated Recording Mission (`run_mission.py`)
- **Direct Execution:** A standalone script that bypasses the GUI scheduler for maximum reliability when launched by Windows Task Scheduler.
- **Arguments:** Accepts duration (seconds), audio device index, and target URL via command line.
- **Wake-from-Sleep:** Designed to run immediately upon system wake (via Task Scheduler configuration).

### 2.2 Browser Automation (`browser_automation.py`)
- **Engine:** Uses Selenium WebDriver (Chrome) with `undetected-chromedriver` techniques to bypass basic bot detection.
- **Smart Playback Logic:**
  - **Ad Handling:** Detects and waits for pre-roll ads (video/audio) to finish.
  - **Popup Dismissal:** Automatically closes "Sign Up" modals and other overlays.
  - **State Monitoring:** continuously checks the "Play" button state (using `data-test-state` and ARIA labels) to ensure audio is playing.
  - **Re-engagement:** Clicks "Play" if the stream pauses or stops unexpectedly (e.g., due to buffering or timeout).
- **Headless Mode Support:** Capable of running without a visible browser window (configurable).

### 2.3 Audio Capture (`main.py` / `sounddevice`)
- **Source:** Records from system audio via "Stereo Mix" or Virtual Audio Cable (WASAPI Loopback).
- **Format:** Captures high-quality WAV (44.1kHz/48kHz, Stereo) initially.
- **Fail-safe:** Logs errors if the audio device is unavailable or disconnected.

### 2.4 Post-Processing & Management
- **Compression:** Automatically converts raw WAV files to MP3 using FFmpeg (configurable bitrate, default 192kbps).
- **Cleanup:** Deletes the original massive WAV file after successful conversion.
- **Retention Policy:** Automatically deletes recordings older than `X` days (configurable in `config.py`) to manage disk space.

### 2.5 Logging & Diagnostics
- **Dual Logging:** Writes to both console (`mission.log` for high-level status) and file (`recording.log` for detailed debugging).
- **Visual Feedback:** GUI (when used) displays real-time status updates from the automation thread.

---

## 3. User Flows

### A. The "Set It and Forget It" Workflow (Primary)
1. **Setup:** User configures `run_mission.bat` with the desired URL, Duration, and Device ID.
2. **Schedule:** User creates a Windows Task to run `run_mission.bat` daily (e.g., at 2:00 AM), with "Wake the computer to run this task" enabled.
3. **Execution:**
   - PC wakes up.
   - Script launches, checks device availability.
   - Browser opens -> Navigates to URL -> Handles Ads -> Clicks Play.
   - Audio recording starts.
   - System monitors playback for the duration.
4. **Completion:**
   - Recording stops.
   - WAV saved -> Converted to MP3.
   - Old files cleaned up.
   - Script exits (optionally shuts down app/PC).

### B. Manual Recording (Ad-hoc)
1. User opens `iheart_gui_v2.py`.
2. Selects Audio Device and Duration.
3. Pastes iHeartRadio URL.
4. Clicks "Start Recording".
5. App follows the same automation logic as the scheduled task.

---

## 4. System Architecture

### Tech Stack
- **Language:** Python 3.11+
- **GUI Framework:** PyQt6 (for the manual interface and QThread management).
- **Browser Automation:** Selenium WebDriver + `webdriver-manager`.
- **Audio Engine:** `sounddevice` (PortAudio wrapper) + `numpy`.
- **Processing:** `ffmpeg-python` / `subprocess` calls to FFmpeg executable.
- **Scheduling:** Windows Task Scheduler (external) + `apscheduler` (internal library use).

### Key Files
- `run_mission.py`: Entry point for scheduled tasks. Initializes Qt and Logging.
- `run_mission.bat`: Wrapper specific for Windows Task Scheduler.
- `browser_automation.py`: `BrowserController` class inheriting from `QThread`. Contains the core logic for navigating the DOM.
- `main.py`: Contains `execute_mission`, audio recording threads (`start_manual_recording`), and file management logic.
- `config.py`: Central configuration for paths (Logs, Downloads, FFmpeg), retention policy, and feature flags.

---

## 5. Configuration & Constraints
- **OS:** Windows 10/11 (Required for "Stereo Mix" / WASAPI loopback implementation specifics).
- **Dependencies:** Google Chrome installed.
- **Hardware:** Requires an audio input device capable of capturing system output (Stereo Mix enabled in Windows Sound Settings).
- **Network:** Stable internet connection required for streaming.
