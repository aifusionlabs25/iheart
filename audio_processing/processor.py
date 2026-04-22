"""
Audio Processor Module

Main coordinator for audio processing pipeline.
Handles the workflow of processing audio files with various enhancement techniques.
"""
import os
import logging
import threading
import time
import traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import shutil

from audio_processing.config import AudioProcessingConfig
from audio_processing.noise_reduction import NoiseReducer


class AudioProcessor:
    """
    Main class for processing audio recordings with various enhancements.
    """
    
    def __init__(self):
        """
        Initialize the audio processor.
        """
        self.config = AudioProcessingConfig.load()
        logging.info("Initializing AudioProcessor")
        
        # Processing queue and lock
        self.processing_queue = []
        self.queue_lock = threading.Lock()
        
        # Initialize worker thread
        self.worker_thread = None
        self.stop_worker_event = Event()
        
        # Initialize processors
        self._init_processors()
    
    def _init_processors(self):
        """Initialize the audio processing components."""
        # Initialize noise reducer if enabled
        self.noise_reducer = None
        if self.config.enable_noise_reduction:
            self.noise_reducer = NoiseReducer(
                strength=self.config.noise_reduction_strength
            )
        
        logging.info("Audio processors initialized")
    
    def start_worker(self):
        """Start the background worker thread for processing the queue."""
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.stop_worker_event.clear()
            self.worker_thread = threading.Thread(
                target=self._process_queue_worker,
                daemon=True
            )
            self.worker_thread.start()
            logging.info("Audio processor worker thread started")
        else:
            logging.info("Worker thread already running")
    
    def shutdown_worker(self, wait=False, timeout=5):
        """Stop the background worker thread, optionally waiting for it."""
        if self.worker_thread and self.worker_thread.is_alive():
            logging.info(f"Requesting audio processor worker shutdown (Wait: {wait}, Timeout: {timeout}s)...")
            self.stop_worker_event.set()
            if wait:
                self.worker_thread.join(timeout=timeout)
                if self.worker_thread.is_alive():
                     logging.warning(f"Audio processor worker thread did not shut down within {timeout}s timeout.")
                else:
                     logging.info("Audio processor worker thread stopped successfully after waiting.")
            else:
                 logging.info("Audio processor worker shutdown requested (no wait). Thread may still be running briefly.")
        else:
             logging.info("Audio processor worker already stopped or not initialized.")
    
    def process_file(self, input_file, output_file=None):
        """
        Process an audio file with the configured enhancements.
        
        Args:
            input_file: Path to the input audio file
            output_file: Optional path for the output file. If None, will use
                         input filename + configured suffix
        
        Returns:
            Path to the processed output file
        """
        if not self.config.enabled:
            logging.info("Audio processing is disabled, skipping")
            return input_file
        
        if not os.path.exists(input_file):
            logging.error(f"Input file not found: {input_file}")
            return None
        
        # Determine output file path if not specified
        if output_file is None:
            filename, ext = os.path.splitext(input_file)
            output_file = f"{filename}{self.config.output_suffix}{ext}"
        
        # Create temporary files for processing stages
        temp_nr = f"{os.path.splitext(input_file)[0]}_enhanced_temp_nr{os.path.splitext(input_file)[1]}"
        
        current_file = input_file
        
        try:
            # Apply noise reduction if enabled
            if self.config.enable_noise_reduction and self.noise_reducer:
                logging.info(f"Applying noise reduction to {current_file}")
                self.noise_reducer.process(current_file, temp_nr)
                current_file = temp_nr
            
            # Copy the final processed file to the output location
            if current_file != input_file:
                shutil.copy2(current_file, output_file)
                logging.info(f"Copied final output to {output_file}")
                
                # Clean up temporary files
                try:
                    if os.path.exists(temp_nr) and temp_nr != output_file:
                        os.remove(temp_nr)
                except Exception as e:
                    logging.warning(f"Could not remove temp file {temp_nr}: {e}")
            else:
                # If no processing was done, just copy the input file
                shutil.copy2(input_file, output_file)
                logging.info(f"No processing applied, copied input to {output_file}")
            
            # Handle original file based on configuration
            if not self.config.preserve_original and input_file != output_file:
                try:
                    os.remove(input_file)
                    logging.info(f"Original file removed: {input_file}")
                except Exception as e:
                    logging.warning(f"Could not remove original file {input_file}: {e}")
            else:
                logging.info(f"Original file preserved: {input_file}")
            
            return output_file
            
        except Exception as e:
            logging.error(f"Error processing audio file {input_file}: {e}")
            logging.error(traceback.format_exc())
            
            # Clean up any temporary files if there was an error
            for temp_file in [temp_nr]:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
            
            raise 

    def queue_file_for_processing(self, input_file):
        """
        Queue a file for background processing.
        
        Args:
            input_file: Path to the input audio file
        """
        with self.queue_lock:
            self.processing_queue.append(input_file)
        
        # Start worker thread if not already running
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.stop_worker_event.clear()
            self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.worker_thread.start()
    
    def _process_queue_worker(self):
        """Background worker that processes the queue."""
        logging.info("Audio processing worker started")
        
        while not self.stop_worker_event.is_set():
            # Check if there are items in the queue
            if not self.processing_queue:
                time.sleep(1)
                continue
            
            # Get the next item
            with self.queue_lock:
                if not self.processing_queue:  # Check again within lock
                    continue
                current_file = self.processing_queue.pop(0)
            
            # Process the file
            try:
                logging.info(f"Processing file from queue: {current_file}")
                result = self.process_file(current_file)
                
                logging.info(f"Completed processing: {current_file} -> {result}")
                
            except Exception as e:
                logging.error(f"Error processing {current_file}: {e}")
                logging.error(traceback.format_exc())
            
            # Small pause to prevent CPU overuse
            time.sleep(0.1)
        
        logging.info("Audio processing worker stopped")
    
    def _process_queue(self):
        """Process files in the queue until empty or stopped."""
        while not self.stop_worker_event.is_set():
            # Get next file from queue
            next_file = None
            with self.queue_lock:
                if self.processing_queue:
                    next_file = self.processing_queue.pop(0)
            
            if next_file:
                try:
                    logging.info(f"Processing queued file: {next_file}")
                    self.process_file(next_file)
                except Exception as e:
                    logging.error(f"Error processing queued file {next_file}: {e}")
            else:
                # No more files to process
                break 