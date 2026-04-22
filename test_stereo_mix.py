import sounddevice as sd
import numpy as np
import time

def test_stereo_mix_signal():
    # Index 18 is Stereo Mix (from previous debug_audio.py output)
    DEVICE_INDEX = 18 
    DURATION = 5  # seconds
    SAMPLE_RATE = 48000
    
    print(f"--- Testing Stereo Mix (Device {DEVICE_INDEX}) ---")
    print("Please play some audio (YouTube, Music, etc.) NOW...")
    for i in range(3, 0, -1):
        print(f"Starting in {i}...")
        time.sleep(1)
        
    print("Recording...")
    try:
        recording = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=2, device=DEVICE_INDEX)
        sd.wait()
        print("Recording finished.")
        
        # Analyze
        max_amp = np.max(np.abs(recording))
        avg_amp = np.mean(np.abs(recording))
        
        print("-" * 30)
        print(f"Max Amplitude: {max_amp:.6f}")
        print(f"Avg Amplitude: {avg_amp:.6f}")
        
        if max_amp < 0.001:
            print("RESULT: SILENCE DETECTED.")
            print("Possible causes:")
            print("1. Stereo Mix volume is muted or set to 0 in Windows Sound Settings.")
            print("2. No audio was playing during the test.")
            print("3. Driver issue.")
        else:
            print("RESULT: AUDIO DETECTED!")
            print("Stereo Mix is working correctly.")
            
    except Exception as e:
        print(f"Error recording: {e}")

if __name__ == "__main__":
    test_stereo_mix_signal()
