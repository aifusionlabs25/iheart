"""
Setup Verification Script for iHeart Recorder
Checks that all required components are properly configured for the new computer.
"""
import os
import sys
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"[OK] Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"[FAIL] Python {version.major}.{version.minor}.{version.micro} is not compatible (requires 3.8+)")
        return False

def check_dependencies():
    """Check if required packages are installed."""
    # Map package names to their import names
    package_imports = {
        'PyQt6': 'PyQt6',
        'numpy': 'numpy',
        'soundfile': 'soundfile',
        'scipy': 'scipy',
        'apscheduler': 'apscheduler',
        'pytz': 'pytz',
        'sounddevice': 'sounddevice',
        'selenium': 'selenium',
        'webdriver_manager': 'webdriver_manager',
        'dotenv': 'dotenv',
        'cryptography': 'cryptography',
        'librosa': 'librosa',
        'matplotlib': 'matplotlib',
        'pyaudio': 'pyaudio',
        'yt_dlp': 'yt_dlp',
        'screeninfo': 'screeninfo'
    }
    
    missing = []
    for package_name, import_name in package_imports.items():
        try:
            __import__(import_name)
            print(f"[OK] {package_name} is installed")
        except ImportError:
            print(f"[FAIL] {package_name} is NOT installed")
            missing.append(package_name)
    
    if missing:
        print(f"\n[WARN] Missing packages: {', '.join(missing)}")
        print("  Install with: pip install -r requirements.txt")
        return False
    return True

def check_config_files():
    """Check if required configuration files exist."""
    base_dir = Path(__file__).parent
    required_files = [
        'config.py',
        'client_secrets.json',
        'audio_processing_config.json'
    ]
    
    all_exist = True
    for file in required_files:
        file_path = base_dir / file
        if file_path.exists():
            print(f"[OK] {file} exists")
        else:
            print(f"[FAIL] {file} is MISSING")
            all_exist = False
    
    return all_exist

def check_environment_variables():
    """Check if environment variables are set (optional)."""
    username = os.environ.get('IHEART_USERNAME', '')
    password = os.environ.get('IHEART_PASSWORD', '')
    
    if username and password:
        print("[OK] IHEART_USERNAME and IHEART_PASSWORD are set")
        return True
    else:
        print("[WARN] IHEART_USERNAME and IHEART_PASSWORD are not set (optional)")
        print("  You can set them in start_recorder.bat or as system environment variables")
        return True  # Not critical

def check_audio_devices():
    """Check if audio devices are available."""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = [d for d in devices if d.get('max_input_channels', 0) > 0]
        
        if input_devices:
            print(f"[OK] Found {len(input_devices)} audio input device(s)")
            print("  Available devices:")
            for i, device in enumerate(devices):
                if device.get('max_input_channels', 0) > 0:
                    print(f"    [{i}] {device.get('name', 'Unknown')}")
            return True
        else:
            print("[FAIL] No audio input devices found")
            return False
    except ImportError:
        print("[WARN] Cannot check audio devices (sounddevice not installed)")
        return False
    except Exception as e:
        print(f"[WARN] Error checking audio devices: {e}")
        return False

def check_chrome():
    """Check if Chrome is installed."""
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"[OK] Google Chrome found at {path}")
            return True
    
    print("[WARN] Google Chrome not found in standard locations")
    print("  ChromeDriver will attempt to download automatically, but Chrome must be installed")
    return True  # Not critical, webdriver_manager will handle it

def check_batch_file():
    """Check if start_recorder.bat has correct path."""
    batch_file = Path(__file__).parent / 'start_recorder.bat'
    if not batch_file.exists():
        print("[FAIL] start_recorder.bat not found")
        return False
    
    with open(batch_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'E:\\AI\\iheart_dev' in content or 'E:/AI/iheart_dev' in content:
            print("[WARN] start_recorder.bat still contains old path (E:\\AI\\iheart_dev)")
            print("  This should be updated to the new location")
            return False
        else:
            print("[OK] start_recorder.bat path appears to be updated")
            return True

def main():
    """Run all checks."""
    print("=" * 60)
    print("iHeart Recorder Setup Verification")
    print("=" * 60)
    print()
    
    results = []
    
    print("1. Python Version Check")
    print("-" * 60)
    results.append(check_python_version())
    print()
    
    print("2. Dependencies Check")
    print("-" * 60)
    results.append(check_dependencies())
    print()
    
    print("3. Configuration Files Check")
    print("-" * 60)
    results.append(check_config_files())
    print()
    
    print("4. Environment Variables Check")
    print("-" * 60)
    results.append(check_environment_variables())
    print()
    
    print("5. Audio Devices Check")
    print("-" * 60)
    results.append(check_audio_devices())
    print()
    
    print("6. Chrome Installation Check")
    print("-" * 60)
    results.append(check_chrome())
    print()
    
    print("7. Batch File Check")
    print("-" * 60)
    results.append(check_batch_file())
    print()
    
    print("=" * 60)
    critical_checks = results[:3]  # Python, dependencies, config files
    if all(critical_checks):
        print("[OK] All critical checks passed! The application should work.")
    else:
        print("[FAIL] Some critical checks failed. Please address the issues above.")
    print("=" * 60)

if __name__ == "__main__":
    main()

