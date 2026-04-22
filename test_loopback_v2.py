import sounddevice as sd
import numpy as np

def test_loopback_v2(device_index):
    print(f"Attempting WASAPI loopback recording on device {device_index} with loopback=True...")
    try:
        # Check if symbol is available
        if not hasattr(sd, 'WasapiSettings'):
            print("sd.WasapiSettings not available in this version of sounddevice.")
            return

        try:
             # Try to open input stream on this output device with loopback=True
             with sd.InputStream(
                 device=device_index, 
                 channels=2, 
                 samplerate=48000, 
                 blocksize=1024,
                 extra_settings=sd.WasapiSettings(loopback=True)
             ) as stream:
                 print("Loopback Stream opened successfully!")
                 print("Recording 2 seconds...")
                 data, overflow = stream.read(48000 * 2) 
                 max_amp = np.max(np.abs(data))
                 print(f"Read {len(data)} frames. Max amplitude: {max_amp}")
                 if max_amp > 0.001:
                     print("Audio detected!")
                 else:
                     print("Silence detected (play some audio to test).")
        except Exception as e:
            print(f"Loopback InputStream failed: {e}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Index 14 is "Speakers (Yeti Stereo Microphone)"
    test_loopback_v2(14) 
