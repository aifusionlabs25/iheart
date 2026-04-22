"""
Quick test script to verify the iHeart Recorder setup is working correctly.
This tests core functionality without launching the full GUI.
"""
import sys
import os

def test_imports():
    """Test that all critical modules can be imported."""
    print("=" * 60)
    print("Testing Module Imports")
    print("=" * 60)
    
    modules_to_test = [
        ('PyQt6', 'PyQt6'),
        ('numpy', 'numpy'),
        ('soundfile', 'soundfile'),
        ('scipy', 'scipy'),
        ('apscheduler', 'apscheduler'),
        ('sounddevice', 'sounddevice'),
        ('selenium', 'selenium'),
        ('webdriver_manager', 'webdriver_manager'),
        ('config', 'config'),
        ('main', 'main'),
    ]
    
    failed = []
    for name, import_name in modules_to_test:
        try:
            __import__(import_name)
            print(f"[OK] {name}")
        except ImportError as e:
            print(f"[FAIL] {name}: {e}")
            failed.append(name)
    
    if failed:
        print(f"\n[WARN] Failed to import: {', '.join(failed)}")
        return False
    else:
        print("\n[OK] All critical modules imported successfully")
        return True

def test_config():
    """Test that configuration loads correctly."""
    print("\n" + "=" * 60)
    print("Testing Configuration")
    print("=" * 60)
    
    try:
        from config import BASE_DIR, SAVE_DIR, LOG_FILE_PATH, CHANNELS, SAMPLE_RATE
        print(f"[OK] Config module loaded")
        print(f"  Base directory: {BASE_DIR}")
        print(f"  Save directory: {SAVE_DIR}")
        print(f"  Log file: {LOG_FILE_PATH}")
        print(f"  Audio settings: {CHANNELS} channels, {SAMPLE_RATE} Hz")
        
        # Check if directories exist or can be created
        if os.path.exists(SAVE_DIR) or os.access(os.path.dirname(SAVE_DIR), os.W_OK):
            print(f"[OK] Save directory is accessible")
        else:
            print(f"[WARN] Save directory may not be writable")
        
        return True
    except Exception as e:
        print(f"[FAIL] Config error: {e}")
        return False

def test_audio_devices():
    """Test that audio devices can be detected."""
    print("\n" + "=" * 60)
    print("Testing Audio Device Detection")
    print("=" * 60)
    
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = [d for d in devices if d.get('max_input_channels', 0) > 0]
        
        if input_devices:
            print(f"[OK] Found {len(input_devices)} audio input device(s)")
            print("\n  Available input devices:")
            for i, device in enumerate(devices):
                if device.get('max_input_channels', 0) > 0:
                    name = device.get('name', 'Unknown')
                    channels = device.get('max_input_channels', 0)
                    print(f"    [{i}] {name} ({channels} channels)")
            
            # Check for Stereo Mix (commonly used for system audio)
            stereo_mix = [d for d in devices if 'stereo mix' in d.get('name', '').lower()]
            if stereo_mix:
                print(f"\n[INFO] Found 'Stereo Mix' device - good for recording system audio")
            
            return True
        else:
            print("[WARN] No audio input devices found")
            return False
    except ImportError:
        print("[FAIL] sounddevice not installed")
        return False
    except Exception as e:
        print(f"[FAIL] Audio device error: {e}")
        return False

def test_main_module():
    """Test that the main recording module loads."""
    print("\n" + "=" * 60)
    print("Testing Main Recording Module")
    print("=" * 60)
    
    try:
        import main
        print("[OK] Main module imported")
        
        # Test that AudioRecorder class exists
        if hasattr(main, 'AudioRecorder'):
            print("[OK] AudioRecorder class available")
            
            # Test device listing
            try:
                devices = main.AudioRecorder.get_audio_devices()
                if devices:
                    print(f"[OK] Can list audio devices ({len(devices)} found)")
                else:
                    print("[WARN] No devices returned (may be normal)")
            except Exception as e:
                print(f"[WARN] Device listing error: {e}")
        else:
            print("[FAIL] AudioRecorder class not found")
            return False
        
        return True
    except Exception as e:
        print(f"[FAIL] Main module error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_module():
    """Test that GUI module can be imported (without launching)."""
    print("\n" + "=" * 60)
    print("Testing GUI Module")
    print("=" * 60)
    
    try:
        # Just test import, don't create QApplication
        import iheart_gui
        print("[OK] GUI module imported")
        
        if hasattr(iheart_gui, 'IHeartRecorderGUI'):
            print("[OK] IHeartRecorderGUI class available")
        else:
            print("[WARN] IHeartRecorderGUI class not found")
        
        return True
    except Exception as e:
        print(f"[FAIL] GUI module error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("iHeart Recorder Setup Test")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print()
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Audio Devices", test_audio_devices()))
    results.append(("Main Module", test_main_module()))
    results.append(("GUI Module", test_gui_module()))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n[OK] All tests passed! The application should be ready to use.")
        print("\nTo test the GUI, run:")
        print("  python iheart_gui.py")
        print("\nTo test the CLI, run:")
        print("  python main.py")
    else:
        print("\n[WARN] Some tests failed. Please review the errors above.")
    
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

