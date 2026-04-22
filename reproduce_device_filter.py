import sounddevice as sd
import logging
from unittest.mock import patch, MagicMock

# Mock the sounddevice.query_devices function
def mock_query_devices():
    return [
        {'name': 'Microsoft Sound Mapper - Input', 'max_input_channels': 2, 'index': 0},
        {'name': 'Stereo Mix (Realtek High Definition Audio)', 'max_input_channels': 2, 'index': 1},
        {'name': 'Primary Sound Capture Driver', 'max_input_channels': 2, 'index': 2},
        {'name': 'Microphone (Realtek HD Audio Mic input)', 'max_input_channels': 2, 'index': 3},
        {'name': 'Speakers (Realtek High Definition Audio)', 'max_input_channels': 0, 'index': 4}, # Output only
        {'name': 'Headphones (Realtek HD Audio 2nd output)', 'max_input_channels': 0, 'index': 5}, # Output only
        {'name': 'Headphones Loopback', 'max_input_channels': 2, 'index': 6}, # Input loopback with "Headphones" in name
    ]

# Import the class to test (we need to import it after patching or patch it where it's used)
# Since we can't easily import main.py without running it, we'll copy the relevant method logic here for testing
# OR we can import main.py if we're careful. Let's try to import main.py but patch sd before calling the method.

import main

def test_get_audio_devices():
    print("Testing AudioRecorder.get_audio_devices filtering logic...")
    
    with patch('sounddevice.query_devices', side_effect=mock_query_devices):
        devices = main.AudioRecorder.get_audio_devices()
        
        print(f"Found {len(devices)} devices after filtering:")
        for dev in devices:
            print(f" - {dev['name']} (Index: {dev['index']})")
            
        # Assertions
        names = [d['name'] for d in devices]
        
        # Should contain:
        assert 'Stereo Mix (Realtek High Definition Audio)' in names
        assert 'Microphone (Realtek HD Audio Mic input)' in names
        
        # Should NOT contain:
        assert 'Microsoft Sound Mapper - Input' not in names
        assert 'Primary Sound Capture Driver' not in names
        assert 'Speakers (Realtek High Definition Audio)' not in names # Output only, filtered by max_input_channels
        assert 'Headphones (Realtek HD Audio 2nd output)' not in names # Output only
        assert 'Headphones Loopback' not in names # Filtered by name "Headphones"
        
        print("\nSUCCESS: Filtering logic works as expected!")

if __name__ == "__main__":
    # Configure logging to see output
    logging.basicConfig(level=logging.INFO)
    test_get_audio_devices()
