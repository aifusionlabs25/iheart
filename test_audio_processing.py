"""
Test script for audio processing functionality.
"""
import os
import argparse
import logging
import time
import soundfile as sf
import numpy as np

from audio_processing import AudioProcessor, AudioProcessingConfig

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                   format="%(asctime)s - %(levelname)s - %(message)s")

def test_audio_processing(file_path=None):
    """
    Test audio processing on a file.
    
    Args:
        file_path: Path to audio file to test with
    """
    if not file_path:
        print("No file specified. Please provide a file path.")
        return
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    # Create a test configuration
    config = AudioProcessingConfig()
    config.enable_noise_reduction = True
    config.noise_reduction_strength = 0.7
    config.preserve_original = True
    
    # Initialize processor
    processor = AudioProcessor()
    
    # Process the file
    try:
        print(f"Processing file: {file_path}")
        start_time = time.time()
        
        # Process the file
        output_file = processor.process_file(file_path)
        
        elapsed_time = time.time() - start_time
        print(f"Processing completed in {elapsed_time:.2f} seconds")
        print(f"Output saved to: {output_file}")
        
        # Print file information
        if os.path.exists(output_file):
            original_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            processed_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
            
            print(f"Original file size: {original_size:.2f} MB")
            print(f"Processed file size: {processed_size:.2f} MB")
            
            # Get audio duration
            try:
                audio_data, sr = sf.read(file_path)
                original_duration = len(audio_data) / sr
                
                audio_data, sr = sf.read(output_file)
                processed_duration = len(audio_data) / sr
                
                print(f"Original duration: {original_duration:.2f} seconds")
                print(f"Processed duration: {processed_duration:.2f} seconds")
            except Exception as e:
                print(f"Error getting audio duration: {e}")
        
    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test audio processing")
    parser.add_argument("--file", help="Path to audio file to test")
    args = parser.parse_args()
    
    test_audio_processing(args.file)

if __name__ == "__main__":
    main() 