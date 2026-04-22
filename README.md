# iHeart Radio Recorder

A desktop application for recording iHeart Radio streams with scheduling, noise reduction, and automatic MP3 compression.

## Features

- **Manual Recording** — Start/stop recording on demand via the GUI or CLI
- **Scheduled Recording** — Automated daily recording using APScheduler (cron-based)
- **Mission Mode** — One-off scheduled recordings with browser automation
- **Browser Automation** — Auto-launches iHeartRadio stream, keeps playback alive, handles popups
- **MP3 Compression** — Automatic WAV → MP3 conversion via FFmpeg
- **Audio Processing** — Optional noise reduction pipeline
- **Silent Capture Mode** — Supports WASAPI loopback capture for recording without audible speaker output (Windows)
- **Boutique GUI** — Custom PyQt6 interface with VU meters, waveform display, and hardware-style controls
- **CLI Mode** — Full headless operation for servers or Task Scheduler

## Requirements

- Python 3.8+
- FFmpeg (for MP3 compression — install via [ffmpeg.org](https://ffmpeg.org/download.html) or place in `ffmpeg/bin/`)
- Google Chrome (for browser automation)

## Installation

1. **Clone this repository:**
   ```bash
   git clone https://github.com/rvicks/iHeartAuto.git
   cd iHeartAuto
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   copy .env.example .env
   ```
   Edit `.env` with your actual credentials (optional — only needed for auto-login and Google Drive upload).

5. **FFmpeg setup:**
   - Option A: Install FFmpeg system-wide and ensure it's on your PATH
   - Option B: Place FFmpeg binary in `ffmpeg/bin/ffmpeg.exe` within the project

## Usage

### GUI Mode (Boutique Edition)
```bash
python iheart_gui.py
```

### GUI with Auto-Schedule
```bash
python iheart_gui.py --auto-schedule
```

### CLI Mode
```bash
python main.py
```

### Direct Mission (Task Scheduler)
```bash
python run_mission.py --duration 14400 --device 18 --url "https://www.iheart.com/live/..."
```

## Project Structure

```
├── main.py                    # Core recording engine & CLI
├── iheart_gui.py              # Boutique Edition GUI (PyQt6)
├── iheart_gui_ww2.py          # WW2 Cockpit GUI theme (alternative)
├── browser_automation.py      # Selenium-based browser control
├── config.py                  # Centralized configuration
├── google_drive_uploader.py   # Google Drive upload integration
├── run_mission.py             # Direct mission runner for Task Scheduler
├── audio_processing/          # Audio enhancement pipeline
│   ├── __init__.py
│   ├── config.py              # Processing configuration
│   ├── noise_reduction.py     # Noise reduction module
│   └── processor.py           # Processing coordinator
├── assets/                    # UI assets
├── resources/                 # UI resources (textures, gauges)
├── docs/                      # Documentation
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
├── start_recorder.bat         # Windows launcher script
└── run_mission.bat            # Windows mission launcher
```

## Configuration

All settings are centralized in `config.py`. Key options:

| Setting | Default | Description |
|---|---|---|
| `ENABLE_COMPRESSION` | `True` | Auto-compress WAV to MP3 after recording |
| `MP3_BITRATE` | `192k` | MP3 encoding quality |
| `DELETE_ORIGINAL_WAV` | `True` | Remove WAV after successful compression |
| `LOCAL_RETENTION_DAYS` | `5` | Auto-delete recordings older than N days |
| `ENABLE_GOOGLE_DRIVE_UPLOAD` | `False` | Upload recordings to Google Drive |
| `CLOSE_APP_ON_COMPLETE` | `False` | Exit app after scheduled recording completes |
| `ENABLE_WASAPI_LOOPBACK` | `True` | Allow selecting WASAPI output devices for silent loopback capture |

Audio processing settings can also be configured via `audio_processing_config.json`.

### Silent Recording on Windows (No Audible Playback)

If you want to record while sleeping (no audible speaker output), use a WASAPI-capable output device with loopback:

1. In device selection, choose an entry labeled with **`[Loopback]`**.
2. Keep your physical speakers muted or volume low/off as needed.
3. The recorder captures the render stream directly via WASAPI loopback.

> Note: Loopback availability depends on your audio driver and host API support in PortAudio/sounddevice.

See `docs/config_reference.md` for full details.

## Security

> ⚠️ **Never commit credentials to version control.**

- Store credentials in a `.env` file (gitignored) or set them as system environment variables
- If using Google Drive upload, obtain OAuth credentials from [Google Cloud Console](https://console.cloud.google.com/apis/credentials) and save as `client_secrets.json` (gitignored)
- See `.env.example` for required variables

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
