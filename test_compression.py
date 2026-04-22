"""
Test script to verify MP3 compression functionality.
"""
import os
import sys
from pathlib import Path

def test_ffmpeg_path():
    """Test if ffmpeg path is correct."""
    print("=" * 60)
    print("Testing FFmpeg Path")
    print("=" * 60)
    
    from config import FFMPEG_PATH
    
    if os.path.exists(FFMPEG_PATH):
        print(f"[OK] FFmpeg found at: {FFMPEG_PATH}")
        return True
    else:
        print(f"[FAIL] FFmpeg not found at: {FFMPEG_PATH}")
        print("  Please verify the path in config.py")
        return False

def test_compression_settings():
    """Test compression configuration."""
    print("\n" + "=" * 60)
    print("Testing Compression Settings")
    print("=" * 60)
    
    from config import ENABLE_COMPRESSION, MP3_BITRATE, DELETE_ORIGINAL_WAV
    
    print(f"Compression Enabled: {ENABLE_COMPRESSION}")
    print(f"MP3 Bitrate: {MP3_BITRATE}")
    print(f"Delete Original WAV: {DELETE_ORIGINAL_WAV}")
    
    if ENABLE_COMPRESSION:
        print("[OK] Compression is enabled")
    else:
        print("[INFO] Compression is disabled")
    
    if MP3_BITRATE in ["128k", "192k", "256k", "320k"]:
        print(f"[OK] Valid bitrate: {MP3_BITRATE}")
    else:
        print(f"[WARN] Bitrate {MP3_BITRATE} may not be valid")
    
    return True

def test_compression_function():
    """Test if compression function can be imported."""
    print("\n" + "=" * 60)
    print("Testing Compression Function")
    print("=" * 60)
    
    try:
        import main
        if hasattr(main.AudioRecorder, '_compress_to_mp3'):
            print("[OK] _compress_to_mp3 method found in AudioRecorder class")
            return True
        else:
            print("[FAIL] _compress_to_mp3 method not found")
            return False
    except Exception as e:
        print(f"[FAIL] Error importing compression function: {e}")
        return False

def main():
    """Run all compression tests."""
    print("\n" + "=" * 60)
    print("MP3 Compression Setup Test")
    print("=" * 60)
    print()
    
    results = []
    results.append(("FFmpeg Path", test_ffmpeg_path()))
    results.append(("Compression Settings", test_compression_settings()))
    results.append(("Compression Function", test_compression_function()))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n[OK] All compression tests passed!")
        print("\nCompression is ready to use.")
        print("\nExpected file size reduction:")
        print("  - 4-hour recording: ~3.8GB WAV -> ~330MB MP3 (192kbps)")
        print("  - Reduction: ~90%")
    else:
        print("\n[WARN] Some tests failed. Please review the errors above.")
    
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

