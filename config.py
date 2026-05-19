"""
Centralized configuration for iHeart Recorder.
All global constants, paths, and environment variable lookups are managed here.
"""
import os
import shutil
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Audio output and log directories
SAVE_DIR = BASE_DIR
LOG_FILE_PATH = str(BASE_DIR / "recording.log")
GUI_LOG_FILE_PATH = str(BASE_DIR / "iheart_recorder_gui.log")
AUDIO_PROCESSING_CONFIG_PATH = str(BASE_DIR / "audio_processing_config.json")

# Environment variables for secrets (do not hardcode in code)
CLIENT_SECRETS_PATH = os.environ.get("CLIENT_SECRETS_PATH", str(BASE_DIR / "client_secrets.json"))
IHEART_USERNAME = os.environ.get("IHEART_USERNAME", "")
IHEART_PASSWORD = os.environ.get("IHEART_PASSWORD", "")

# Audio settings
CHANNELS = 2
SAMPLE_RATE = 44100
CHUNK_SIZE = 4096
AUDIO_FORMAT = "float32"  # Use string for portability

# Capture settings
# If enabled, selecting a WASAPI output device in the UI will use loopback capture,
# allowing silent recording without requiring audible speaker playback.
ENABLE_WASAPI_LOOPBACK = True

# Compression settings
ENABLE_COMPRESSION = True  # Enable automatic MP3 compression after recording
MP3_BITRATE = "192k"  # MP3 bitrate: "128k", "192k", "256k", "320k" (192k recommended for radio)
DELETE_ORIGINAL_WAV = False  # Keep WAV files so post-recording verification can inspect them
# FFmpeg path: auto-discover from local bundle, system PATH, or common WinGet install
_ffmpeg_local = BASE_DIR / "ffmpeg" / "bin" / "ffmpeg.exe"
_ffmpeg_path = shutil.which("ffmpeg")
_ffmpeg_winget_root = (
    Path.home()
    / "AppData"
    / "Local"
    / "Microsoft"
    / "WinGet"
    / "Packages"
    / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
)
_ffmpeg_winget_matches = sorted(_ffmpeg_winget_root.glob("ffmpeg-*/*/ffmpeg.exe"))
if _ffmpeg_local.exists():
    FFMPEG_PATH = str(_ffmpeg_local)
elif _ffmpeg_path:
    FFMPEG_PATH = _ffmpeg_path
elif _ffmpeg_winget_matches:
    FFMPEG_PATH = str(_ffmpeg_winget_matches[-1])
else:
    FFMPEG_PATH = "ffmpeg"

# Google Drive settings
ENABLE_GOOGLE_DRIVE_UPLOAD = False
GOOGLE_DRIVE_FOLDER_NAME = "iHeart Recordings"

# Scheduler settings (example)
SCHEDULE_TIME = "06:00"  # Temporary scheduled time (HH:MM) for testing at 6:00 AM

# Local file retention settings
LOCAL_RETENTION_DAYS = 5  # Delete local recordings older than this many days

# Auto-shutdown settings
CLOSE_APP_ON_COMPLETE = False  # Close the application after scheduled recording completes

# Add additional configuration as needed
RESOURCES_DIR = str(BASE_DIR / "resources")
COCKPIT_FONT = "Courier New"
COLOR_AMBER = "#ffb84d"
COLOR_GREEN = "#33ff33"

# Usage:
# from config import LOG_FILE_PATH, SAVE_DIR, ...
