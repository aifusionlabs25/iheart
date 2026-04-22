"""
Direct Mission Runner for iHeart Recorder
Executes a recording mission immediately. Designed for Task Scheduler.
Usage: python run_mission.py [duration_seconds] [device_index] [url]
"""
import sys
import logging
import argparse
from datetime import datetime
import os

# Import main first (it configures logging on import, which we will override/add to)
import main
import config

# Import PyQt6 for Event Loop
from PyQt6.QtWidgets import QApplication

# Re-configure logging to ensure we have BOTH File and Stream handlers
# main.py might have cleared them, so we force our own configuration here.
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Ensure StreamHandler exists (for mission.log)
has_stream = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
if not has_stream:
    logger.addHandler(logging.StreamHandler(sys.stdout))

# Ensure FileHandler exists (for recording.log)
has_file = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
if not has_file:
    try:
        file_handler = logging.FileHandler(config.LOG_FILE_PATH)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to setup file logging: {e}")

# We don't use basicConfig because main.py might have messed with root logger already.


def run_direct_mission():
    parser = argparse.ArgumentParser(description="Run iHeart Recorder Mission Immediately")
    # Default duration: ~4 hours (14340 sec from original code logic? No, let's default to 4h)
    # Original code had logic: stop_time - start_time. 
    # Let's default to 4 hours (14400s) if not specified.
    parser.add_argument("--duration", type=int, default=14400, help="Duration in seconds (default: 4 hours)")
    parser.add_argument("--device", type=int, default=None, help="Audio Device Index (default: auto-detect)")
    parser.add_argument("--url", type=str, default="https://www.iheart.com/live/newsradio-830-khvh-4748/", help="Target URL")
    
    args = parser.parse_args()
    
    print("="*60)
    print(f"STARTING DIRECT MISSION at {datetime.now()}")
    print(f"Target: {args.url}")
    print(f"Device Index: {args.device}")
    print(f"Duration: {args.duration} seconds ({args.duration/3600:.2f} hours)")
    print("="*60)
    
    try:
        # Create QApplication for QThread/WebEngine support
        # This is required for BrowserController (which uses QThread) to work
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
            
        print("QApplication Initialized.")
        
        # Execute mission (this blocks until done)
        main.execute_mission(args.url, args.duration, args.device)
        
        print("="*60)
        print("MISSION COMPLETE")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\nMission aborted by user.")
    except Exception as e:
        logging.error(f"Mission Failed: {e}", exc_info=True)
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_direct_mission()
