import sounddevice as sd
import sys

def list_devices():
    print("--- Audio Device Check ---")
    try:
        devices = sd.query_devices()
        default_in, default_out = sd.default.device
        
        print(f"Default Input Device: {default_in}")
        print(f"Default Output Device: {default_out}")
        print("-" * 50)
        
        for i, dev in enumerate(devices):
            name = dev.get('name')
            in_channels = dev.get('max_input_channels')
            out_channels = dev.get('max_output_channels')
            sample_rate = dev.get('default_samplerate')
            
            mark = " "
            if i == default_in: mark = ">"
            if "Stereo Mix" in name: mark = "*"
            
            hostapi = dev.get('hostapi')
            print(f"{mark} [{i}] {name}")
            print(f"    In: {in_channels}, Out: {out_channels}, Rate: {sample_rate}, HostAPI: {hostapi}")
            
    except Exception as e:
        print(f"Error querying devices: {e}")

if __name__ == "__main__":
    list_devices()
