import sounddevice as sd
import numpy as np

def test_loopback(device_index):
    print(f"Attempting loopback recording on device {device_index}...")
    try:
        # Check if it's WASAPI
        dev = sd.query_devices(device_index)
        print(f"Device: {dev['name']}, HostAPI: {dev['hostapi']}")
        
        # Try to open input stream on this output device
        # We need to specify 'loopback=True' in extra_settings if supported, 
        # but sounddevice determines this automatically or requires specific handling.
        # Actually, strict PortAudio WASAPI Loopback requires using the WASAPI specific structure.
        # But let's try standard sounddevice first.
        
        try:
             # Recent sounddevice versions might need 'loopback=True' in some contexts,
             # or we just try to open it as input.
             with sd.InputStream(device=device_index, channels=2, samplerate=48000, blocksize=1024) as stream:
                 print("Stream opened successfully!")
                 data, overflow = stream.read(48000) # Record 1 second
                 print(f"Read {len(data)} frames. Max amplitude: {np.max(np.abs(data))}")
                 if np.max(np.abs(data)) > 0:
                     print("Audio detected!")
                 else:
                     print("Silence detected (or no audio playing).")
        except Exception as e:
            print(f"Standard InputStream failed: {e}")
            
            # Try with loopback=True (if supported by this version of sounddevice/PortAudio)
            # This is often sounddevice.wasapi.InputStream or requires checking documentation.
            # Let's try to see if sd has WASAPI specific settings accessible easily.
            pass

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Index 14 is "Speakers (Yeti Stereo Microphone)" which is an output device
    test_loopback(14) 
