import os
import queue
import logging
from datetime import datetime, time, timedelta
import time as time_module
from apscheduler.schedulers.background import BackgroundScheduler
import threading
import sounddevice as sd
import numpy as np
import pytz
import traceback
import sys # Added for CLI logging to stdout
from functools import partial # Needed for scheduler job args
import wave
import subprocess
from browser_automation import BrowserController # Added import

# --- Mission / One-Off Logic ---
def execute_mission(url, duration, device_index):
    """
    Executes a 'Mission': Launches browser to URL, records audio, and cleans up.
    Running in a separate thread (APScheduler job).
    """
    logging.info(f"MISSION START: Target={url}, Duration={duration}s")
    
    # 1. Launch Browser
    browser = BrowserController(url)
    browser.start() # Starts QThread
    
    # Wait for browser to load (simple sleep for now, could be improved)
    time_module.sleep(15)
    
    # 2. Start Recording
    # We use start_manual_recording because it's effectively a manual session triggered by automation
    # vs the internal daily schedule logic.
    if start_manual_recording(device_index=device_index, duration=duration):
        logging.info("Mission Recording Started.")
    else:
        logging.error("Mission Recording Failed to Start!")
        browser.stop()
        return

    # 3. Wait for Duration
    # We need to wait here because this function is the job. 
    # If we exit, the browser thread might get killed if not carefully managed, 
    # but more importantly we need to stop the recording at the end.
    # start_manual_recording runs its OWN thread, so we just sleep here.
    
    # Wait loop
    elapsed = 0
    while elapsed < duration:
        time_module.sleep(1)
        elapsed += 1
        
    # 4. Stop Logic
    logging.info("Mission Duration Reached. RTB (Returning to Base).")
    stop_manual_recording()
    browser.stop()
    
    # 5. Cleanup / Upload handled by stop_manual_recording internal logic
    
    if CLOSE_APP_ON_COMPLETE:
        logging.info("Mission Complete. Shutting down system.")
        os._exit(0)

def schedule_one_off_mission(run_date, url, duration, device_index):
    """
    Schedules a one-off mission.
    run_date: datetime object
    """
    global scheduler_instance
    
    if not scheduler_instance:
         # Init scheduler if not running (lazy init)
         start_scheduler(device_index=device_index, test_mode=False) # Helper to start it up
         
    if not scheduler_instance or not scheduler_instance.running:
        logging.error("Scheduler not running, cannot schedule mission.")
        return False
        
    try:
        scheduler_instance.add_job(
            execute_mission, 
            'date', 
            run_date=run_date,
            args=[url, duration, device_index],
            id=f'mission_{int(time_module.time())}'
        )
        logging.info(f"Mission Scheduled for {run_date}")
        return True
    except Exception as e:
        logging.error(f"Failed to schedule mission: {e}")
        return False
# subprocess is imported at line 15

# Import centralized configuration
from config import (
    SAVE_DIR, LOG_FILE_PATH, CHANNELS, SAMPLE_RATE, CHUNK_SIZE, AUDIO_FORMAT,
    ENABLE_COMPRESSION, MP3_BITRATE, DELETE_ORIGINAL_WAV, FFMPEG_PATH,
    SCHEDULE_TIME, ENABLE_GOOGLE_DRIVE_UPLOAD,
    LOCAL_RETENTION_DAYS, CLOSE_APP_ON_COMPLETE, ENABLE_WASAPI_LOOPBACK
)
# GoogleDriveUploader disabled
# from google_drive_uploader import GoogleDriveUploader

# Import the audio processor
try:
    from audio_processing import AudioProcessor, AudioProcessingConfig
except ImportError as import_err:
    logging.error(f"Failed to import audio_processing module: {import_err}. Processing disabled.")
    AudioProcessor = None # Ensure variable exists even if import fails
    AudioProcessingConfig = None

# --- Configuration ---
os.makedirs(SAVE_DIR, exist_ok=True)

# --- Setup Logging ---
# This setup will be used if the file is run directly (CLI mode).
# If imported by iheart_gui.py, the GUI's logging setup takes precedence.
# Configure root logger
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')
log_level = logging.INFO # Default level

# File handler
file_handler = logging.FileHandler(LOG_FILE_PATH)
file_handler.setFormatter(log_formatter)

# Stream handler (for CLI output)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(log_formatter)

# Get the root logger and add handlers
# Note: Adding handlers here might cause duplicate logs if GUI also configures root logger.
# A better approach is often to use named loggers. For simplicity now, we configure root.
logger = logging.getLogger()
# Clear existing handlers if any (important if re-running setup)
if logger.hasHandlers():
    logger.handlers.clear()
logger.addHandler(file_handler)
# Add stream handler only if running as main script? Could check __name__
# logger.addHandler(stream_handler) # Add console output for CLI debugging
logger.setLevel(log_level)

# --- Audio settings ---
AUDIO_FORMAT_NP = np.float32 # Use numpy dtype for sounddevice
SAMPLE_WIDTH_BYTES = np.dtype(AUDIO_FORMAT_NP).itemsize # Bytes per sample

# --- Global State ---
# manual_recording_active = False
# scheduled_recording_active = False
manual_recording_thread = None # Keep track of the manual recording thread
scheduled_recording_thread = None # Keep track of the scheduled recording thread
# recording_event = threading.Event() # Controls the recording loop execution
# pause_event = threading.Event()     # Controls pausing within the loop
scheduler_instance = None           # Holds the APScheduler instance
# current_recorder_instance = None    # Holds reference to the active AudioRecorder instance

manual_recorder_instance = None # Hold reference to the manual recorder instance
scheduled_recorder_instance = None # Hold reference to the scheduled recorder instance


# --- Initialize Audio Processor ---
audio_processor = None
audio_processing_enabled = True # Default, can be overridden by GUI/config
if AudioProcessor: # Check if import succeeded
    try:
        # audio_processor = AudioProcessor(config_path=config_path) # OLD
        audio_processor = AudioProcessor() # Initialize without config_path
        logging.info("Audio processor initialized successfully.") # Updated log message
        # Update global state based on loaded config
        audio_processing_enabled = audio_processor.config.enabled # CORRECTED
    except Exception as e:
        logging.error(f"Failed to initialize audio processor: {e}", exc_info=True)
        audio_processing_enabled = False
else:
    logging.warning("AudioProcessor class not available. Audio processing disabled.")
    audio_processing_enabled = False

# --- File Cleanup Function ---
def cleanup_old_recordings():
    """
    Delete local audio recordings older than LOCAL_RETENTION_DAYS.
    Only deletes .wav and .mp3 files in SAVE_DIR.
    """
    if LOCAL_RETENTION_DAYS <= 0:
        logging.info("Cleanup disabled (LOCAL_RETENTION_DAYS <= 0).")
        return 0
    
    cutoff_time = datetime.now() - timedelta(days=LOCAL_RETENTION_DAYS)
    deleted_count = 0
    
    logging.info(f"Running cleanup: Deleting files older than {LOCAL_RETENTION_DAYS} days (before {cutoff_time})...")
    
    try:
        for filename in os.listdir(SAVE_DIR):
            if not (filename.endswith('.wav') or filename.endswith('.mp3')):
                continue
            
            filepath = os.path.join(SAVE_DIR, filename)
            if not os.path.isfile(filepath):
                continue
            
            file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            if file_mtime < cutoff_time:
                try:
                    os.remove(filepath)
                    logging.info(f"Deleted old file: {filename} (modified: {file_mtime})")
                    deleted_count += 1
                except Exception as del_err:
                    logging.warning(f"Failed to delete {filename}: {del_err}")
    except Exception as e:
        logging.error(f"Error during cleanup: {e}", exc_info=True)
    
    logging.info(f"Cleanup complete. Deleted {deleted_count} file(s).")
    return deleted_count

# --- Audio Recorder Class ---
class AudioRecorder:
    """Handles the actual audio recording using sounddevice."""
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.recording_thread = None
        self.stop_event = threading.Event()
        self.recording_event = threading.Event()
        self.pause_event = threading.Event()
        self.device_index = None
        self.selected_device_name = "Unknown"
        self.recording_samplerate = 44100  # Default, updated at recording time
        self.duration = None
        self.frames = [] # Retained from original, as it's used later
        self.start_time = None # Retained
        self.pause_time = None # Retained
        self.total_pause_duration = 0 # Retained
        self.last_progress_log_time = 0 # Retained
        
        # Google Drive Upload disabled
        self.drive_uploader = None

    @staticmethod
    def get_audio_devices():
        """Returns a list of recordable devices (inputs + optional WASAPI loopback outputs)."""
        devices_list = []
        try:
            devices = sd.query_devices()
            hostapis = sd.query_hostapis()
            if not devices:
                logging.warning("No audio devices found by sounddevice.")
                return []
            for i, device in enumerate(devices):
                device_name = device.get('name', f'Unknown Device {i}')
                lower_name = device_name.lower()
                max_input_channels = int(device.get('max_input_channels', 0))
                max_output_channels = int(device.get('max_output_channels', 0))
                hostapi_index = int(device.get('hostapi', -1))
                hostapi_name = ""
                if 0 <= hostapi_index < len(hostapis):
                    hostapi_name = hostapis[hostapi_index].get('name', '')
                hostapi_lower = hostapi_name.lower()

                # Keep light filtering for known placeholder devices only.
                excluded_keywords = [
                    "microsoft sound mapper",
                    "primary sound capture driver",
                    "primary sound driver",
                ]
                if any(keyword in lower_name for keyword in excluded_keywords):
                    continue

                is_standard_input = max_input_channels > 0
                is_wasapi_output = (
                    ENABLE_WASAPI_LOOPBACK
                    and max_input_channels == 0
                    and max_output_channels > 0
                    and "wasapi" in hostapi_lower
                )

                if not (is_standard_input or is_wasapi_output):
                    continue

                display_name = device_name
                if is_wasapi_output:
                    display_name = f"{device_name} [Loopback]"

                devices_list.append({
                    'index': i,
                    'name': display_name,
                    'loopback': is_wasapi_output
                })
            logging.info(f"Found {len(devices_list)} input devices.")
        except Exception as e:
            logging.error(f"Error querying audio devices: {e}", exc_info=True)
        return devices_list

    @staticmethod
    def log_audio_devices():
        """Log available audio devices for debugging."""
        logging.info("--- Querying Audio Devices ---")
        try:
            devices = sd.query_devices()
            if not devices:
                logging.warning("No audio devices found by sounddevice.")
                return
            logging.info("Available audio devices:")
            for i, device in enumerate(devices):
                try:
                    default_sr = device.get('default_samplerate', 'N/A')
                    logging.info(
                        f"  Device {i}: {device.get('name', 'Unknown Name')} "
                        f"(In: {device.get('max_input_channels', 'N/A')}, "
                        f"Out: {device.get('max_output_channels', 'N/A')}, "
                        f"Default SR: {default_sr})"
                    )
                except Exception as dev_log_err:
                    logging.error(f"  Error querying details for device {i}: {dev_log_err}")
            # Log default devices
            try:
                 default_input_idx, default_output_idx = sd.default.device
                 logging.info(f"Default Input Device Index: {default_input_idx} | Name: {sd.query_devices(default_input_idx)['name']}")
                 logging.info(f"Default Output Device Index: {default_output_idx} | Name: {sd.query_devices(default_output_idx)['name']}")
            except Exception as default_err:
                 logging.error(f"Could not query default devices: {default_err}")

        except Exception as e:
            logging.error(f"Error querying audio devices: {e}", exc_info=True)
        logging.info("--- End Audio Device Query ---")


    def start_recording(self, device_index, duration=None, progress_callback=None):
        try:
            self.device_index = device_index
            use_loopback = False
            max_input_channels = CHANNELS
            max_output_channels = CHANNELS
            try:
                device_info = sd.query_devices(device=self.device_index)
                self.selected_device_name = device_info.get('name', f'Device {self.device_index}')
                max_input_channels = int(device_info.get('max_input_channels', 0))
                max_output_channels = int(device_info.get('max_output_channels', 0))
                hostapi_idx = int(device_info.get('hostapi', -1))
                hostapi_name = ""
                if hostapi_idx >= 0:
                    hostapi_name = sd.query_hostapis(hostapi_idx).get('name', '')
                use_loopback = (
                    ENABLE_WASAPI_LOOPBACK
                    and max_input_channels == 0
                    and max_output_channels > 0
                    and "wasapi" in hostapi_name.lower()
                    and hasattr(sd, "WasapiSettings")
                )

                # Use device's native sample rate to avoid resampling artifacts
                native_samplerate = int(device_info.get('default_samplerate', 44100))
                self.recording_samplerate = native_samplerate
                logging.info(f"Using native sample rate: {native_samplerate} Hz for {self.selected_device_name}")
            except Exception as e:
                self.selected_device_name = f'Device {self.device_index} (Name query failed: {e})'
                self.recording_samplerate = 44100  # Fallback
                max_input_channels = CHANNELS
                max_output_channels = CHANNELS
                logging.warning(f"Could not query device {self.device_index}: {e}. Using fallback 44100 Hz.")

            self.duration = duration
            self.progress_callback = progress_callback
            self.frames = []
            self.start_time = time_module.time()
            self.last_progress_log_time = self.start_time
            self.total_pause_duration = 0
            self.is_recording = True
            self.is_paused = False

            self.recording_event.set()  # Ensure event is set

            # Start the stream and keep thread alive
            selected_channels = CHANNELS
            extra_settings = None
            if use_loopback:
                selected_channels = max(1, min(CHANNELS, max_output_channels))
                extra_settings = sd.WasapiSettings(loopback=True)
                logging.info(
                    f"Using WASAPI loopback capture on device {self.selected_device_name} "
                    f"(channels={selected_channels})."
                )
            else:
                selected_channels = max(1, min(CHANNELS, max_input_channels))

            with sd.InputStream(
                device=self.device_index,
                channels=selected_channels,
                samplerate=self.recording_samplerate,
                callback=self.audio_callback,
                blocksize=1024,
                extra_settings=extra_settings
            ):
                logging.info(f"Started recording on {self.selected_device_name} (Index: {self.device_index}) at {self.recording_samplerate} Hz")
                while self.recording_event.is_set():
                    time_module.sleep(0.1)  # Keep thread alive

            # After exiting the loop, save the recording
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            device_info_name = "Dev" + "".join(c if c.isalnum() else '_' for c in self.selected_device_name)
            if self.duration:
                filename = os.path.join(SAVE_DIR, f"Rec_{timestamp}_{device_info_name}_{int(self.duration)}s.wav")
            else:
                filename = os.path.join(SAVE_DIR, f"Rec_{timestamp}_{device_info_name}.wav")
            self._save_recording(filename)
            self.is_recording = False
            logging.info(f"Recording stopped and file saved: {filename}")
            return True

        except Exception as e:
            logging.error(f"Error starting recording: {str(e)}")
            self.is_recording = False
            return False

    def _save_recording(self, filename):
        """Save the recorded frames to a WAV file. Splits into 1-hour chunks if needed."""
        if not self.frames:
            logging.warning(f"Save called, but no frames recorded for {filename}. Skipping save.")
            return # Don't save an empty file

        logging.info(f"Attempting to save {len(self.frames)} frames ({len(self.frames)*CHUNK_SIZE} samples) to {filename}")
        combined_frames = self.frames # Keep original list for now
        self.frames = [] # Clear frames immediately to free memory

        try:
            # Concatenate frames into a single NumPy array
            audio_data = np.concatenate(combined_frames, axis=0)
            logging.info(f"Concatenated audio data shape: {audio_data.shape}, dtype: {audio_data.dtype}")
            logging.info(f"Total frames: {len(combined_frames)}, total samples: {audio_data.shape[0]}, expected duration: {audio_data.shape[0]/self.recording_samplerate:.2f} seconds")

            # Warn if duration is much less than 4 hours (for scheduled recordings)
            actual_duration = audio_data.shape[0] / self.recording_samplerate
            if actual_duration < 0.95 * 4 * 3600:  # Less than 95% of 4 hours
                logging.warning(f"Recording duration ({actual_duration/60:.1f} min) is much shorter than expected (4 hours). Possible early stop or error.")

            # Convert float32 audio data to int16 for standard WAV
            audio_data = np.clip(audio_data, -1.0, 1.0) # Clip first
            if np.any(np.isnan(audio_data)) or np.any(np.isinf(audio_data)):
                 logging.error(f"NaN or Inf detected in audio data for {filename}. Cannot save correctly.")
                 raise ValueError("Invalid values (NaN/Inf) found in audio data.")

            audio_data_int16 = (audio_data * 32767).astype(np.int16)
            logging.debug("Converted audio data to int16.")

            # --- Chunked Saving ---
            max_samples_per_file = self.recording_samplerate * 3600  # 1 hour per file
            total_samples = audio_data_int16.shape[0]
            num_chunks = (total_samples + max_samples_per_file - 1) // max_samples_per_file
            base, ext = os.path.splitext(filename)
            for chunk_idx in range(num_chunks):
                start = chunk_idx * max_samples_per_file
                end = min((chunk_idx + 1) * max_samples_per_file, total_samples)
                chunk_data = audio_data_int16[start:end]
                if len(chunk_data) == 0:
                    logging.warning(f"Skipping empty chunk {chunk_idx+1} for {filename}")
                    continue  # Don't write empty/silent files
                chunk_filename = f"{base}_part{chunk_idx+1}{ext}" if num_chunks > 1 else filename
                with wave.open(chunk_filename, 'wb') as wf:
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(chunk_data.dtype.itemsize) # Should be 2 for int16
                    wf.setframerate(self.recording_samplerate)
                    wf.writeframes(chunk_data.tobytes())
                logging.info(f"Successfully wrote WAV file: {chunk_filename}")
                try:
                    actual_duration = len(chunk_data) / self.recording_samplerate
                    file_size_mb = os.path.getsize(chunk_filename) / (1024 * 1024)
                    logging.info(
                        f"Recording chunk saved successfully:\n"
                        f"  - File: {chunk_filename}\n"
                        f"  - Duration: {actual_duration:.2f} seconds ({timedelta(seconds=actual_duration)})\n"
                        f"  - Size: {file_size_mb:.2f} MB"
                    )
                except Exception as stat_err:
                    logging.warning(f"Could not get final stats for saved file {chunk_filename}: {stat_err}")

            # --- Compression ---
            if ENABLE_COMPRESSION:
                try:
                    for chunk_idx in range(num_chunks):
                        chunk_filename = f"{base}_part{chunk_idx+1}{ext}" if num_chunks > 1 else filename
                        if not os.path.exists(chunk_filename):
                            continue  # Only compress files that were actually written
                        self._compress_to_mp3(chunk_filename)
                except Exception as compress_err:
                    logging.error(f"Error compressing files for {filename}: {compress_err}", exc_info=True)
            # --- End Compression ---

            # --- Post-processing ---
            global audio_processor, audio_processing_enabled # Use globals
            if audio_processing_enabled and audio_processor:
                try:
                    for chunk_idx in range(num_chunks):
                        # Use compressed MP3 if available, otherwise use WAV
                        chunk_filename = f"{base}_part{chunk_idx+1}{ext}" if num_chunks > 1 else filename
                        if ENABLE_COMPRESSION and DELETE_ORIGINAL_WAV:
                            # Check if MP3 was created
                            mp3_filename = os.path.splitext(chunk_filename)[0] + ".mp3"
                            if os.path.exists(mp3_filename):
                                chunk_filename = mp3_filename
                        
                        if not os.path.exists(chunk_filename):
                            continue  # Only process files that were actually written
                        logging.info(f"Queueing saved file for post-processing: {chunk_filename}")
                        if hasattr(audio_processor, 'queue_file_for_processing'):
                            audio_processor.queue_file_for_processing(chunk_filename)
                        else:
                            logging.warning("AudioProcessor does not have queue_file_for_processing, processing directly...")
                            audio_processor.process_file(chunk_filename)
                except Exception as process_err:
                    logging.error(f"Error queueing/starting audio post-processing for {filename}: {process_err}", exc_info=True)
            # --- End Post-processing ---

        except MemoryError:
             logging.error(f"MemoryError while concatenating or converting {len(combined_frames)} frames for {filename}. Try reducing recording duration or check system RAM.", exc_info=True)
             print(f"ERROR: Ran out of memory trying to save {filename}. Recording lost.")
        except Exception as e:
            logging.error(f"Error saving recording {filename}: {e}", exc_info=True)
            print(f"ERROR: Failed to save recording {filename}: {e}")
        finally:
             # Ensure frames are cleared even if save fails midway
             combined_frames = None # Allow garbage collection


    def _compress_to_mp3(self, wav_filename):
        """
        Compress a WAV file to MP3 using ffmpeg.
        
        Args:
            wav_filename: Path to the WAV file to compress
        """
        if not os.path.exists(wav_filename):
            logging.warning(f"Cannot compress {wav_filename}: file does not exist")
            return False
        
        if not os.path.exists(FFMPEG_PATH):
            logging.warning(f"FFmpeg not found at {FFMPEG_PATH}. Compression disabled.")
            return False
        
        try:
            # Generate MP3 filename
            base, ext = os.path.splitext(wav_filename)
            mp3_filename = base + ".mp3"
            
            logging.info(f"Compressing {wav_filename} to MP3 (bitrate: {MP3_BITRATE})...")
            
            # Build ffmpeg command
            # -i: input file
            # -codec:a libmp3lame: use MP3 encoder
            # -b:a: audio bitrate
            # -y: overwrite output file without asking
            # -loglevel error: only show errors (suppress normal output)
            cmd = [
                FFMPEG_PATH,
                "-i", wav_filename,
                "-codec:a", "libmp3lame",
                "-b:a", MP3_BITRATE,
                "-y",  # Overwrite output
                "-loglevel", "error",  # Suppress verbose output
                mp3_filename
            ]
            
            # Run ffmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout (should be much faster)
            )
            
            if result.returncode == 0:
                # Compression successful
                wav_size_mb = os.path.getsize(wav_filename) / (1024 * 1024)
                mp3_size_mb = os.path.getsize(mp3_filename) / (1024 * 1024)
                reduction_percent = (1 - mp3_size_mb / wav_size_mb) * 100
                
                logging.info(
                    f"Compression successful:\n"
                    f"  - Original: {wav_filename} ({wav_size_mb:.2f} MB)\n"
                    f"  - Compressed: {mp3_filename} ({mp3_size_mb:.2f} MB)\n"
                    f"  - Reduction: {reduction_percent:.1f}%"
                )
                
                # Delete original WAV if configured
                if DELETE_ORIGINAL_WAV:
                    try:
                        os.remove(wav_filename)
                        logging.info(f"Deleted original WAV file: {wav_filename}")
                    except Exception as del_err:
                        logging.warning(f"Failed to delete original WAV file {wav_filename}: {del_err}")
                
                # Upload disabled
                # if self.drive_uploader: ...

                return True
            else:
                # Compression failed
                error_msg = result.stderr if result.stderr else "Unknown error"
                logging.error(f"FFmpeg compression failed for {wav_filename}: {error_msg}")
                # Clean up partial MP3 file if it exists
                if os.path.exists(mp3_filename):
                    try:
                        os.remove(mp3_filename)
                    except Exception:
                        pass
                return False
                
        except subprocess.TimeoutExpired:
            logging.error(f"FFmpeg compression timed out for {wav_filename}")
            return False
        except Exception as e:
            logging.error(f"Error compressing {wav_filename} to MP3: {e}", exc_info=True)
            return False

    def _cleanup(self):
        """Reset recorder state after recording finishes or fails."""
        self.frames = [] # Ensure frames list is empty
        self.start_time = None
        self.pause_time = None
        self.total_pause_duration = 0
        self.last_progress_log_time = 0
        logging.debug(f"AudioRecorder internal state cleaned up for device {self.selected_device_name}.")

    def audio_callback(self, indata, frames, time, status):
        """Callback function for audio recording."""
        if status:
            logging.warning(f"Audio callback status: {status}")
        if hasattr(self, 'is_recording') and hasattr(self, 'is_paused'):
            if self.is_recording and not self.is_paused:
                self.frames.append(indata.copy())
                try:
                    rms = np.sqrt(np.mean(indata**2))
                    if rms > 0.0001:
                        # Convert to dBFS. 
                        dbfs = 20 * np.log10(rms)
                        # Offset to push typical Windows audio (-30 to -15 dBFS) into the -20 to +3 VU range
                        # Adding +25 means a -25 dBFS signal registers as 0 on the VU meter.
                        self.current_vu = dbfs + 25 
                    else:
                        self.current_vu = -40
                except Exception:
                    self.current_vu = -40


# --- Recording Control Functions (called by GUI or CLI) ---

def start_manual_recording(device_index=None, duration=None):
    """Starts a manual recording session in a separate thread."""
    global manual_recording_thread, manual_recorder_instance, scheduled_recording_thread
    if manual_recording_thread and manual_recording_thread.is_alive():
        msg = "Manual recording is already active."
        print(msg)
        logging.warning(msg)
        return False # Indicate that recording was not started

    # Check if a scheduled recording is currently active
    if scheduled_recording_thread and scheduled_recording_thread.is_alive():
        msg = "Cannot start manual recording: A scheduled recording is currently active."
        print(msg)
        logging.warning(msg)
        return False

    try:
        # Create a new recorder instance for this recording
        manual_recorder_instance = AudioRecorder()

        # Determine filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Get device name for filename if possible, otherwise use index
        device_info_name = "DevUnknown"
        if device_index is not None:
             try:
                 device_info = sd.query_devices(device=device_index)
                 # Sanitize device name for filename
                 device_info_name = "Dev" + "".join(c if c.isalnum() else '_' for c in device_info.get('name', str(device_index)))
             except Exception:
                 device_info_name = f"Dev{device_index}"
        else:
             try:
                  default_input_idx, _ = sd.default.device
                  device_info = sd.query_devices(device=default_input_idx)
                  # Sanitize device name for filename
                  device_info_name = "Dev" + "".join(c if c.isalnum() else '_' for c in device_info.get('name', str(default_input_idx)))
             except Exception:
                  device_info_name = "DevDefault"

        filename = os.path.join(SAVE_DIR, f"ManRec_{timestamp}_{device_info_name}.wav")

        # Set flags *before* starting thread (critical for state management)
        # manual_recording_active = True # Removed global flag
        # recording_event.set() # Removed global event
        # pause_event.clear()   # Removed global event

        # Start the recording in a daemon thread
        manual_recording_thread = threading.Thread(
            target=manual_recorder_instance.start_recording, # Use instance method
            args=(device_index, duration, None), # Pass device_index directly
            name=f"ManualRec-{device_info_name}", # More descriptive thread name
            daemon=True # Allows main program to exit even if this thread hangs (use with caution)
        )
        manual_recording_thread.start()

        # Log and print confirmation
        duration_str = f"{duration/3600:.1f} hours" if duration else "indefinitely"
        msg = f"Manual recording started on device index {device_index} for {duration_str}, saving to {filename}"
        logging.info(msg)
        print(msg)
        # Also log which device name was actually selected
        try:
             # Accessing selected_device_name directly from the instance
             logging.info(f"Actual device used for manual recording: {manual_recorder_instance.selected_device_name}")
             print(f"Manual Recording started successfully on device index {device_index} for {duration_str}. (Device: {manual_recorder_instance.selected_device_name})")
        except Exception as name_err:
             logging.warning(f"Could not get selected device name after starting manual recording: {name_err}")
             print(f"Manual Recording started successfully on device index {device_index} for {duration_str}.")

        return True # Indicate successful start

    except Exception as e:
        # Reset state on failure to start
        # manual_recording_active = False # Removed global flag
        manual_recording_thread = None
        manual_recorder_instance = None # Clear global ref on failure
        logging.error(f"Failed to start manual recording thread: {e}", exc_info=True)
        print(f"ERROR: Failed to start manual recording: {e}")
        return False # Indicate failure


def pause_manual_recording():
    """Pauses the current manual recording."""
    global manual_recorder_instance
    if manual_recorder_instance and manual_recorder_instance.recording_event.is_set() and not manual_recorder_instance.pause_event.is_set():
        manual_recorder_instance.pause_event.set()
        # Logging now happens within the recorder loop when pause state changes
        print("Manual recording paused.")
        return True
    elif not manual_recorder_instance or not manual_recorder_instance.recording_event.is_set():
        print("No manual recording is active to pause.")
        return False
    else:
         print("Manual recording is already paused.")
         return False

def resume_manual_recording():
    """Resumes the current manual recording."""
    global manual_recorder_instance
    if manual_recorder_instance and manual_recorder_instance.recording_event.is_set() and manual_recorder_instance.pause_event.is_set():
        # Logging now happens within the recorder loop when pause state changes
        manual_recorder_instance.pause_event.clear()
        print("Manual recording resumed.")
        return True
    elif not manual_recorder_instance or not manual_recorder_instance.recording_event.is_set():
        print("No manual recording is active to resume.")
        return False
    else:
         print("Manual recording is not paused.")
         return False


def stop_manual_recording():
    """Stops the current manual recording session."""
    global manual_recording_thread, manual_recorder_instance
    if not manual_recording_thread or not manual_recording_thread.is_alive():
        msg = "No manual recording is currently active to stop."
        print(msg)
        logging.warning(msg)
        # Ensure state is clean even if thread is unexpectedly not alive
        manual_recording_thread = None
        manual_recorder_instance = None
        return False # Indicate that recording was not active

    logging.info("Attempting to stop manual recording...")
    print("Attempting to stop manual recording...")

    try:
        # 1. Signal the recording thread to stop its loop
        manual_recorder_instance.recording_event.clear()
        # 2. Ensure it's not stuck waiting on the pause event
        manual_recorder_instance.pause_event.clear()

        # 3. Wait for the recording thread to finish (includes saving the file)
        thread_to_join = manual_recording_thread # Store reference before potentially clearing it
        logging.info(f"Waiting for manual recording thread ({thread_to_join.name}) to finish...")
        thread_to_join.join(timeout=60) # Add a reasonable timeout (e.g., 60 seconds)

        if thread_to_join.is_alive():
             logging.warning(f"Manual recording thread {thread_to_join.name} did not finish within 60s timeout!")
             print(f"Warning: Recording thread did not stop cleanly within timeout. It may still be running or may not have saved correctly.")
             # Depending on desired behavior, might force exit or leave it
             # For now, proceed with state cleanup but log warning
        else:
             logging.info(f"Manual recording thread {thread_to_join.name} joined.")
             print("Manual recording stopped.")
             recording_stopped = True # Indicate successful stop signal and join

        # 4. Update global state *after* attempting to join thread
        # manual_recording_active = False # Removed global flag
        manual_recording_thread = None # Clear the global thread reference
        manual_recorder_instance = None # Clear the instance reference

        logging.info("Manual recording stop process completed.")
        return True # Indicate stop process initiated/completed

    except Exception as e:
        logging.error(f"Error stopping manual recording thread: {e}", exc_info=True)
        print(f"ERROR: An error occurred while stopping recording: {e}")
        # Force state reset on error
        # manual_recording_active = False # Removed global flag
        manual_recording_thread = None
        manual_recorder_instance = None
        return False # Indicate error during stop


# --- Scheduled Recording Control (via APScheduler jobs) ---
def _start_scheduled_recording_job(device_index=None):
    """Function executed by the scheduler to start recording."""
    global scheduled_recording_thread, scheduled_recorder_instance, manual_recording_thread
    logging.info("SCHEDULER JOB: _start_scheduled_recording_job triggered.")

    if scheduled_recording_thread and scheduled_recording_thread.is_alive():
        logging.warning("SCHEDULER JOB: Scheduled recording start job triggered, but recording seems already active. Ignoring.")
        return # Exit if recording is already active

    # Check if a manual recording is currently active
    if manual_recording_thread and manual_recording_thread.is_alive():
        logging.warning("SCHEDULER JOB: Cannot start scheduled recording: A manual recording is currently active.")
        return

    try:
        # Create a new recorder instance for this scheduled recording
        scheduled_recorder_instance = AudioRecorder()

        # Determine filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Get device name for filename if possible, otherwise use index
        device_info_name = "DevUnknown"
        if device_index is not None:
             try:
                 device_info = sd.query_devices(device=device_index)
                 # Sanitize device name for filename
                 device_info_name = "Dev" + "".join(c if c.isalnum() else '_' for c in device_info.get('name', str(device_index)))
             except Exception:
                 device_info_name = f"Dev{device_index}"
        else:
             try:
                  default_input_idx, _ = sd.default.device
                  device_info = sd.query_devices(device=default_input_idx)
                  # Sanitize device name for filename
                  device_info_name = "Dev" + "".join(c if c.isalnum() else '_' for c in device_info.get('name', str(default_input_idx)))
             except Exception:
                  device_info_name = "DevDefault"

        filename = os.path.join(SAVE_DIR, f"SchRec_{timestamp}_{device_info_name}.wav")

        # Start the recording in a daemon thread
        # Duration is NOT passed here; the stop job will handle duration
        scheduled_recording_thread = threading.Thread(
            target=scheduled_recorder_instance.start_recording, # Use instance method
            args=(device_index, None, None), # Pass device_index directly
            name=f"ScheduledRec-{device_info_name}", # More descriptive thread name
            daemon=True # Allows main program to exit even if this thread hangs (use with caution)
        )
        scheduled_recording_thread.start()

        # Update global state AFTER successfully starting thread
        # scheduled_recording_active = True # Removed global flag
        # recording_thread = thread # Removed global thread ref
        # scheduled_recorder_instance is already set above

        logging.info(f"SCHEDULER JOB: Scheduled recording started successfully. File: {filename}")

    except Exception as e:
        logging.error(f"SCHEDULER JOB: FAILED to start scheduled recording: {e}", exc_info=True)
        # Reset state if start failed
        # scheduled_recording_active = False # Removed global flag
        scheduled_recording_thread = None
        scheduled_recorder_instance = None

    logging.info("SCHEDULER JOB: _start_scheduled_recording_job finished.")

def _stop_scheduled_recording_job():
    """Function executed by the scheduler to stop recording."""
    global scheduled_recording_thread, scheduled_recorder_instance
    logging.info("SCHEDULER JOB: _stop_scheduled_recording_job triggered.")

    if not scheduled_recording_thread or not scheduled_recording_thread.is_alive():
        logging.warning("SCHEDULER JOB: Scheduled recording stop job triggered, but recording wasn't active or thread is not alive. Ignoring.")
        # Ensure state is clean
        scheduled_recording_thread = None
        scheduled_recorder_instance = None
        return # Exit if recording is not active

    logging.info("SCHEDULER JOB: Attempting to stop scheduled recording...")

    try:
        # 1. Signal the recording thread to stop its loop using the instance-specific event
        if scheduled_recorder_instance:
             scheduled_recorder_instance.recording_event.clear()
             # Ensure it's not stuck waiting on the pause event (though less likely for scheduled)
             scheduled_recorder_instance.pause_event.clear()

        # 2. Wait for the recording thread to finish (important to ensure file is saved)
        thread_to_join = scheduled_recording_thread # Store reference before potentially clearing it
        logging.info(f"SCHEDULER JOB: Waiting for scheduled recording thread ({thread_to_join.name}) to finish...")
        
        # INCREASED TIMEOUT: Wait up to 10 minutes for compression and upload
        thread_to_join.join(timeout=600) 

        if thread_to_join.is_alive():
             logging.warning(f"SCHEDULER JOB: Recording thread {thread_to_join.name} did not finish within 600s timeout! It may be killed by app exit.")
             # Depending on desired behavior, might force exit or leave it
             # For now, proceed with state cleanup but log warning
        else:
             logging.info(f"SCHEDULER JOB: Recording thread {thread_to_join.name} joined.")

        # 3. Update global state AFTER attempting stop
        scheduled_recording_thread = None
        scheduled_recorder_instance = None # Clear instance ref

        logging.info("SCHEDULER JOB: Scheduled recording stop process completed.")

        # 4. Run file cleanup
        logging.info("SCHEDULER JOB: Running file cleanup...")
        cleanup_old_recordings()

        # 5. Auto-close app if enabled
        if CLOSE_APP_ON_COMPLETE:
            logging.info("SCHEDULER JOB: CLOSE_APP_ON_COMPLETE is enabled.")
            logging.info("SCHEDULER JOB: Closing application immediately.")
            try:
                # Forcefully exit the process to ensure all threads (GUI, etc.) are killed
                os._exit(0)
            except Exception as shutdown_err:
                logging.error(f"SCHEDULER JOB: Failed to exit application: {shutdown_err}")

    except Exception as e:
        logging.error(f"SCHEDULER JOB: FAILED to stop scheduled recording cleanly: {e}", exc_info=True)
        # Attempt to reset state even on error
        scheduled_recording_thread = None
        scheduled_recorder_instance = None

    logging.info("SCHEDULER JOB: _stop_scheduled_recording_job finished.")

def start_scheduler(device_index=None, test_mode=False, test_delay_minutes=2):
    """Sets up and starts the APScheduler for daily recordings. If test_mode is True, schedules a job a few minutes from now for testing."""
    global scheduler_instance, scheduled_recording_thread
    if scheduler_instance and scheduler_instance.running:
        msg = "Scheduler is already running."
        print(msg)
        logging.warning(msg)
        return False # Indicate scheduler already running

    logging.info(f"Setting up and starting scheduler (Target Device Index: {device_index}).")
    try:
        # Ensure any previous instance is shut down cleanly
        if scheduler_instance:
             try:
                  scheduler_instance.shutdown(wait=False)
                  logging.info("Shutdown previous scheduler instance.")
             except Exception as shut_err:
                  logging.warning(f"Error shutting down previous scheduler: {shut_err}")
             scheduler_instance = None # Clear ref even if shutdown failed

        # --- Determine Device Index for Scheduled Job ---
        schedule_device_index = device_index # Use the index passed from GUI/CLI
        logging.info(f"Scheduler will use device index: {schedule_device_index} for jobs.")
        # ---

        # Initialize scheduler with timezone
        phoenix_tz = pytz.timezone('America/Phoenix')
        scheduler = BackgroundScheduler(
            job_defaults={'misfire_grace_time': 300}, # 5 min grace time if scheduler wakes late
            timezone=phoenix_tz
        )

        # Add jobs, passing the device index using functools.partial
        start_job_func = partial(_start_scheduled_recording_job, device_index=schedule_device_index)
        logging.info(f"About to schedule job with function: {repr(start_job_func)} (type: {type(start_job_func)})")
        
        if test_mode:
            # Calculate a start time a few minutes from now
            now = datetime.now(phoenix_tz)
            test_time = now + timedelta(minutes=test_delay_minutes)
            test_hour = test_time.hour
            test_minute = test_time.minute
            logging.info(f"[TEST MODE] Scheduling job at {test_hour}:{test_minute} (now: {now})")
            scheduler.add_job(
                start_job_func,
                'cron',
                hour=test_hour,
                minute=test_minute,
                id='start_scheduled_recording',
                misfire_grace_time=900,
                coalesce=True,
                replace_existing=True
            )
            logging.info(f"[TEST MODE] Scheduled recording start job added: hour={test_hour}, minute={test_minute}, misfire_grace_time=900, coalesce=True, replace_existing=True")
            job = scheduler.get_job('start_scheduled_recording')
            next_run = getattr(job, 'next_run_time', None)
            logging.info(f"[TEST MODE] Job object: {repr(job)}")
            logging.info(f"[TEST MODE] Job.func_ref: {repr(getattr(job, 'func_ref', None))}")
            if next_run:
                logging.info(f"[TEST MODE] Next scheduled recording start: {next_run}")
            else:
                logging.info("[TEST MODE] Next scheduled recording start time not available (job may not be fully scheduled yet).")
        else:
            # --- Adjusted for 11:04 PM start time (hour=23, minute=4) ---
            scheduler.add_job(
                start_job_func,
                'cron',
                hour=23,
                minute=4,
                id='start_scheduled_recording',
                misfire_grace_time=900,  # 15 minutes grace period
                coalesce=True,
                replace_existing=True
            )
            logging.info(f"Scheduled recording start job added: hour=23, minute=4, misfire_grace_time=900, coalesce=True, replace_existing=True")
            job = scheduler.get_job('start_scheduled_recording')
            next_run = getattr(job, 'next_run_time', None)
            logging.info(f"Job object: {repr(job)}")
            logging.info(f"Job.func_ref: {repr(getattr(job, 'func_ref', None))}")
            if next_run:
                logging.info(f"Next scheduled recording start: {next_run}")
            else:
                logging.info("Next scheduled recording start time not available (job may not be fully scheduled yet).")
        # Stop job at 3:04 AM
        scheduler.add_job(_stop_scheduled_recording_job, 'cron', hour=3, minute=4, id='stop_scheduled_recording', replace_existing=True)
        logging.info("Scheduled start and stop jobs added to scheduler.")

        scheduler.start()
        scheduler_instance = scheduler # Store instance globally

        # --- NEW DIAGNOSTIC LOGGING ---
        logging.info(f"Scheduler running: {scheduler.running}")
        jobs = scheduler.get_jobs()
        for job in jobs:
            logging.info(f"Job: {job.id}, next_run_time: {job.next_run_time}, func: {job.func_ref}")

        logging.info(f"APScheduler started successfully in timezone: {phoenix_tz}.")
        device_name = f"Device Index {schedule_device_index}" if schedule_device_index is not None else "Default Input Device"
        if test_mode:
            print(f"[TEST MODE] Scheduled recording enabled for {device_name} (in {test_delay_minutes} minutes from now)")
        else:
            print(f"Scheduled recording enabled for {device_name} (Daily 11:04 PM - 3:04 AM Arizona Time)")
        return True # Indicate success

    except Exception as e:
        logging.error(f"Failed to initialize or start scheduler: {e}", exc_info=True)
        print(f"ERROR: Failed to set up scheduled recording: {e}")
        if 'scheduler' in locals() and scheduler and scheduler.running:
             try: scheduler.shutdown(wait=False)
             except: pass
        scheduler_instance = None # Ensure instance is None on failure
        return False # Indicate failure


def stop_scheduler(): # Manual stop from GUI/CLI
    """Stops the scheduler and cancels any active scheduled recording."""
    global scheduler_instance, scheduled_recording_thread, scheduled_recorder_instance
    logging.info(f"Manual stop requested for scheduler and scheduled recording (Scheduler Running: {scheduler_instance.running if scheduler_instance else False}, Recording Active: {scheduled_recording_thread is not None and scheduled_recording_thread.is_alive()})") # Check if thread exists and is alive
    scheduler_stopped = False
    recording_stopped = False

    # 1. Shutdown Scheduler first to prevent new jobs firing
    if scheduler_instance and scheduler_instance.running:
        try:
            logging.info("Shutting down scheduler instance...")
            scheduler_instance.shutdown(wait=False) # Don't wait for pending jobs to finish
            scheduler_instance = None # Clear instance immediately after shutdown call
            scheduler_stopped = True
            logging.info("Scheduler shut down successfully.")
        except Exception as e:
            logging.error(f"Error shutting down scheduler: {e}", exc_info=True)
            scheduler_instance = None # Clear instance even on error
            print(f"Error stopping scheduler: {e}")
    else:
        logging.info("Scheduler instance not found or already stopped.")

    # 2. Stop Active Scheduled Recording Thread (if any)
    if scheduled_recording_thread and scheduled_recording_thread.is_alive(): # Check if thread exists and is alive
        logging.info("Signaling active scheduled recording thread to stop...")
        try:
            # Use instance-specific events to stop the scheduled recorder
            if scheduled_recorder_instance:
                 scheduled_recorder_instance.recording_event.clear()
                 scheduled_recorder_instance.pause_event.clear() # Ensure not paused

            thread_to_join = scheduled_recording_thread
            if thread_to_join and thread_to_join.is_alive(): # Double check before joining
                logging.info(f"Waiting for scheduled recording thread ({thread_to_join.name}) to finish...")
                thread_to_join.join(timeout=60) # Add a timeout

                if thread_to_join.is_alive():
                     logging.warning(f"Scheduled recording thread {thread_to_join.name} did not finish within 60s timeout!")
                     print("Warning: Scheduled recording thread did not stop cleanly within timeout.")
                else:
                     logging.info(f"Scheduled recording thread {thread_to_join.name} joined.")

            # Update state *after* attempting stop
            # scheduled_recording_active = False # Removed global flag
            scheduled_recording_thread = None
            scheduled_recorder_instance = None # Clear instance ref
            recording_stopped = True
            logging.info("Active scheduled recording stopped manually.")

        except Exception as e:
            logging.error(f"Error stopping active scheduled recording: {e}", exc_info=True)
            print(f"Error stopping active recording: {e}")
            # Force state consistency on error
            # scheduled_recording_active = False # Removed global flag
            scheduled_recording_thread = None
            scheduled_recorder_instance = None
    else:
        logging.info("No scheduled recording was active to stop.")

    # Return overall status
    return scheduler_stopped and (recording_stopped or not scheduled_recording_thread) # True if scheduler stopped and recording was stopped or not active


# --- Stream Readiness Check for Scheduled Recording ---
def is_stream_ready(max_wait_seconds=60, check_interval=2):
    """
    Checks if the stream/browser is ready. Waits up to max_wait_seconds, polling every check_interval seconds.
    Returns True if ready, False otherwise.
    """
    import time
    waited = 0
    while waited < max_wait_seconds:
        try:
            # Import GUI module dynamically to access stream_active
            import sys
            if 'iheart_gui' in sys.modules:
                gui_mod = sys.modules['iheart_gui']
            else:
                import iheart_gui as gui_mod
            # Check stream_active
            if hasattr(gui_mod, 'main_window') and hasattr(gui_mod.main_window, 'stream_active'):
                if gui_mod.main_window.stream_active:
                    logging.info(f"Stream readiness check: stream_active is True after {waited}s.")
                    return True
            elif hasattr(gui_mod, 'stream_active'):
                if gui_mod.stream_active:
                    logging.info(f"Stream readiness check: stream_active is True after {waited}s.")
                    return True
        except Exception as e:
            logging.warning(f"Stream readiness check: Exception while checking stream_active: {e}")
        time.sleep(check_interval)
        waited += check_interval
    logging.warning(f"Stream readiness check: Stream not ready after {max_wait_seconds}s.")
    return False


# --- Main CLI Loop (if run directly) ---
def main_cli():
    """Main function to run the recorder via Command Line Interface."""
    global manual_recording_thread, scheduled_recording_thread, scheduler_instance
    global audio_processor, audio_processing_enabled

    # Ensure root logger has stream handler for CLI visibility if run directly
    if __name__ == "__main__" and not any(isinstance(h, logging.StreamHandler) for h in logging.getLogger().handlers):
        logger = logging.getLogger()
        if not logger.handlers: # Add handlers only if none exist
            logger.addHandler(file_handler)
            logger.addHandler(stream_handler)
            logger.setLevel(log_level) # Ensure level is set

    logging.info("--- Starting iHeart Recorder (CLI Mode) ---")
    print("\n--- iHeart Radio Recorder - Command Line Interface ---")
    print("====================================================")
    AudioRecorder.log_audio_devices() # Log devices on startup

    # Main interaction loop
    while True:
        print("\n--- Options ---")
        print(" 1. Start Manual Recording")
        print(" 2. Pause/Resume Manual Recording")
        print(" 3. Stop Manual Recording")
        print(" 4. Enable Scheduled Recording (11:04 PM - 3:04 AM AZ)")
        print(" 5. Disable Scheduled Recording")
        print(" 6. Run Audio Diagnostic Tests")
        print(" 7. Configure Audio Processing")
        print(" 8. List Audio Devices")
        print(" 9. Exit")

        print("\n--- Status ---")
        sched_running = scheduler_instance.running if scheduler_instance else False
        print(f"- Manual Recording:   {'ACTIVE' if manual_recording_thread and manual_recording_thread.is_alive() else 'Inactive'}") # Check if thread exists and is alive
        print(f"- Scheduler Enabled:  {'YES' if sched_running else 'NO'}")
        print(f"- Scheduled Rec Now:  {'ACTIVE' if scheduled_recording_thread and scheduled_recording_thread.is_alive() else 'Inactive'}") # Check if thread exists and is alive
        # Use processor's check for enabled status
        proc_enabled = audio_processor.config.enabled if audio_processor else False # CORRECTED
        print(f"- Audio Processing:   {'Enabled' if proc_enabled else 'Disabled'}")


        choice = input("\nEnter your choice: ").strip()

        try: # Added master try block for loop
            if choice == '1':
                if manual_recording_thread and manual_recording_thread.is_alive(): # Check if thread exists and is alive
                    print("Manual recording already active.")
                    continue
                # Device Selection
                devices = AudioRecorder.get_audio_devices()
                print("\nAvailable Input Devices:")
                if not devices:
                    print("  No input devices found!")
                    continue
                for dev in devices:
                    print(f"  {dev['index']}: {dev['name']}")
                try:
                    def_idx, _ = sd.default.device
                except ValueError:
                     def_idx = -1 # No default device
                     print("Warning: No default input device found.")

                dev_choice = input(f"Enter device index (leave blank for default: {def_idx if def_idx != -1 else 'N/A'}): ").strip()
                selected_device_index = None
                if dev_choice.isdigit():
                    selected_device_index = int(dev_choice)
                elif not dev_choice and def_idx != -1: # Use default if blank and default exists
                     selected_device_index = def_idx
                elif not dev_choice and def_idx == -1:
                     print("No default input device available. Please select an index.")
                     continue
                elif not dev_choice: # Should not happen if def_idx check above works, but belt-and-suspenders
                     print("Invalid selection. Please enter a device index.")
                     continue


                # Duration Selection
                dur_choice = input("Enter duration in hours (e.g., 1.5, leave blank for no limit): ").strip()
                selected_duration_sec = None
                if dur_choice:
                    try:
                         selected_duration_sec = float(dur_choice) * 3600
                    except ValueError:
                         print("Invalid duration format. Recording indefinitely.")
                         selected_duration_sec = None
                # Start
                start_manual_recording(device_index=selected_device_index, duration=selected_duration_sec)

            elif choice == '2': # Pause/Resume Toggle
                global manual_recorder_instance # Need to access the instance
                if not manual_recorder_instance or not manual_recorder_instance.recording_event.is_set(): # Check if instance exists and is recording
                    print("No manual recording active.")
                    continue

                if manual_recorder_instance.pause_event.is_set(): # Check instance-specific pause event
                    resume_manual_recording()
                else:
                    pause_manual_recording()

            elif choice == '3':
                stop_manual_recording()

            elif choice == '4':
                 if scheduler_instance and scheduler_instance.running: # Check if scheduler is running
                      print("Scheduler already enabled.")
                      continue
                 # Device Selection for Schedule
                 devices = AudioRecorder.get_audio_devices()
                 print("\nAvailable Input Devices for Schedule:")
                 if not devices:
                      print("  No input devices found!")
                      continue
                 for dev in devices:
                      print(f"  {dev['index']}: {dev['name']}")
                 try:
                      def_idx, _ = sd.default.device
                 except ValueError:
                      def_idx = -1
                      print("Warning: No default input device found.")

                 dev_choice = input(f"Enter device index for schedule (leave blank for default: {def_idx if def_idx != -1 else 'N/A'}): ").strip()
                 selected_device_index = None
                 if dev_choice.isdigit():
                     selected_device_index = int(dev_choice)
                 elif not dev_choice and def_idx != -1:
                      selected_device_index = def_idx
                 elif not dev_choice and def_idx == -1:
                      print("No default input device available. Please select an index.")
                      continue
                 elif not dev_choice:
                      print("Invalid selection. Please enter a device index.")
                      continue

                 start_scheduler(device_index=selected_device_index)

            elif choice == '5':
                stop_scheduler() # This stops scheduler AND active scheduled recording

            elif choice == '6':
                print("Audio diagnostic tests are not yet implemented in this version.")
                logging.info("User selected audio diagnostic tests (not implemented).")


            elif choice == '7':
                configure_audio_processing_cli() # Use CLI specific config function

            elif choice == '8':
                 AudioRecorder.log_audio_devices() # List devices again

            elif choice == '9':
                print("Exiting...")
                # Perform cleanup
                if manual_recording_thread and manual_recording_thread.is_alive(): stop_manual_recording() # Attempt graceful stop if thread is alive
                if scheduler_instance and scheduler_instance.running: stop_scheduler() # Attempt graceful stop
                if audio_processor: audio_processor.shutdown_worker(wait=False) # CORRECTED CALL (don't wait in CLI exit)
                logging.info("--- iHeart Recorder CLI Shutdown ---")
                # Close log handlers? Usually handled by Python exit
                break # Exit the while loop

            else:
                print("Invalid choice. Please try again.")

        except Exception as cli_err: # Catch errors within loop iteration
             logging.error(f"Error in CLI main loop iteration: {cli_err}", exc_info=True)
             print(f"\nAn unexpected error occurred: {cli_err}")
             # Consider whether to continue or exit on error


def configure_audio_processing_cli():
    """CLI menu for configuring audio processing via AudioProcessor."""
    global audio_processor, audio_processing_enabled

    if not AudioProcessor:
         print("\nAudio processing module (audio_processing.py) could not be imported.")
         logging.warning("Attempted to configure audio processing, but module not loaded.")
         return

    # Ensure processor instance exists if possible
    if audio_processor is None:
         try:
              # audio_processor = AudioProcessor(config_path=config_path) # OLD
              audio_processor = AudioProcessor() # Initialize without config_path
              audio_processing_enabled = audio_processor.config.enabled # CORRECTED
              logging.info("Initialized audio processor for configuration.")
         except Exception as e:
              print(f"\nError initializing audio processor: {e}")
              logging.error(f"Failed to initialize audio processor for config: {e}", exc_info=True)
              return # Cannot configure if it doesn't initialize

    # Main config loop
    while True:
        # Reload config state at start of each loop iteration for accurate display
        config = audio_processor.config
        current_status = audio_processor.config.enabled # CORRECTED

        print("\n--- Audio Processing Config (CLI) ---")
        print(f" Status: {'ENABLED' if current_status else 'DISABLED'}")
        print("-" * 35)
        print(f"[1] Toggle Enable/Disable Processing")
        print(f"[2] Noise Reduction: {'Enabled' if config.enable_noise_reduction else 'Disabled'}")
        print(f"[3]    Strength: {config.noise_reduction_strength:.2f} (0.0-1.0, requires NR enabled)")
        print(f"[4] Preserve Original File: {'Yes' if config.preserve_original else 'No'}")
        print(f"[5] Processed File Suffix: '{config.output_suffix}'")
        print("[6] Save Changes and Return")
        print("[7] Discard Changes and Return")

        choice = input("Select option: ").strip()

        try: # Added try block for choice handling
            if choice == '1':
                 if current_status:
                      if hasattr(audio_processor, 'disable'): audio_processor.disable() # Check if method exists
                      print("Audio processing DISABLED.")
                 else:
                      if hasattr(audio_processor, 'enable'): audio_processor.enable() # Check if method exists
                      print("Audio processing ENABLED.")
                 # Update global flag after toggling state
                 audio_processing_enabled = audio_processor.config.enabled # CORRECTED

            elif choice == '2':
                 config.enable_noise_reduction = not config.enable_noise_reduction
                 print(f"Noise Reduction toggled to: {'Enabled' if config.enable_noise_reduction else 'Disabled'}")
                 # Apply immediately to internal config object
                 if hasattr(audio_processor, 'update_config'): audio_processor.update_config(config) # Check method exists

            elif choice == '3':
                 if not config.enable_noise_reduction:
                      print("Enable Noise Reduction (Option 2) before setting strength.")
                      continue # Skip rest of this iteration
                 strength_in = input(f"Enter strength [0.0-1.0] (current: {config.noise_reduction_strength:.2f}): ").strip()
                 if strength_in:
                     try:
                         strength = float(strength_in)
                         config.noise_reduction_strength = max(0.0, min(1.0, strength))
                         print(f"Strength set to {config.noise_reduction_strength:.2f}")
                         if hasattr(audio_processor, 'update_config'): audio_processor.update_config(config) # Check method exists
                     except ValueError:
                         print("Invalid input. Strength unchanged.")

            elif choice == '4':
                 config.preserve_original = not config.preserve_original
                 print(f"Preserve Original toggled to: {'Yes' if config.preserve_original else 'No'}")
                 if hasattr(audio_processor, 'update_config'): audio_processor.update_config(config) # Check method exists

            elif choice == '5':
                 suffix_in = input(f"Enter suffix (current: '{config.output_suffix}', e.g., _processed): ").strip()
                 # Basic validation: ensure suffix doesn't create hidden files or invalid paths
                 if suffix_in and not suffix_in.startswith('.') and '/' not in suffix_in and '\\' not in suffix_in:
                      config.output_suffix = suffix_in
                      print(f"Suffix set to '{config.output_suffix}'")
                      if hasattr(audio_processor, 'update_config'): audio_processor.update_config(config) # Check method exists
                 elif not suffix_in: # Allow setting empty suffix
                       config.output_suffix = ""
                       print("Suffix set to empty (processed files will overwrite originals if Preserve=No).")
                       if hasattr(audio_processor, 'update_config'): audio_processor.update_config(config) # Check method exists
                 else:
                      print("Invalid suffix. Not changed.")

            elif choice == '6': # Save and Return
                 if hasattr(audio_processor, 'save_config') and audio_processor.save_config():
                     print("Configuration saved successfully.")
                 else:
                     print("ERROR saving configuration to file (method missing or failed).")
                 break # Exit config loop

            elif choice == '7': # Discard and Return
                 print("Changes discarded.")
                 # Reload config from file to discard in-memory changes
                 if hasattr(audio_processor, 'load_config'): audio_processor.load_config() # Check method exists
                 # Update global flag based on loaded config
                 audio_processing_enabled = audio_processor.config.enabled # CORRECTED
                 break # Exit config loop

            else:
                 print("Invalid option.")

        except Exception as conf_err: # Catch errors within choice handling
             logging.error(f"Error during audio processing configuration choice: {conf_err}", exc_info=True)
             print(f"An error occurred: {conf_err}")


# --- Entry Point ---
if __name__ == "__main__":
    # Make sure SAVE_DIR exists (redundant but safe)
    os.makedirs(SAVE_DIR, exist_ok=True)

    # Setup logging specifically for CLI execution
    # (Ensures console output and file logging for direct runs)
    logger = logging.getLogger()
    # Add handlers only if they aren't already present
    has_file_handler = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
    has_stream_handler = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
    if not has_file_handler:
        logger.addHandler(file_handler)
    if not has_stream_handler:
        logger.addHandler(stream_handler)
    logger.setLevel(log_level) # Ensure level is set

    # Log the start of the CLI session
    logging.info("="*20 + " CLI Mode Initialized " + "="*20)

    # Run the CLI main function
    main_cli()

    # Optional: Log CLI shutdown
    logging.info("="*20 + " CLI Mode Exiting " + "="*20)

    # Optional: Explicitly close handlers on exit? Generally not needed.
    # for handler in logger.handlers[:]: logger.removeHandler(handler); handler.close()
