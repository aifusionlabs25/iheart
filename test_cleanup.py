"""
Test script for cleanup_old_recordings function.
Creates test files with different ages and verifies cleanup works correctly.
"""
import os
import sys
import time
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SAVE_DIR, LOCAL_RETENTION_DAYS

def test_cleanup():
    print("=== Testing cleanup_old_recordings ===")
    print(f"SAVE_DIR: {SAVE_DIR}")
    print(f"LOCAL_RETENTION_DAYS: {LOCAL_RETENTION_DAYS}")
    
    # Create test files
    test_files = []
    
    # Old file (should be deleted)
    old_file = os.path.join(SAVE_DIR, "test_old_recording.mp3")
    with open(old_file, "w") as f:
        f.write("old test file")
    # Set modification time to 10 days ago
    old_time = time.time() - (10 * 24 * 60 * 60)
    os.utime(old_file, (old_time, old_time))
    test_files.append(("OLD", old_file))
    
    # New file (should NOT be deleted)
    new_file = os.path.join(SAVE_DIR, "test_new_recording.mp3")
    with open(new_file, "w") as f:
        f.write("new test file")
    test_files.append(("NEW", new_file))
    
    print("\nCreated test files:")
    for label, filepath in test_files:
        mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
        print(f"  [{label}] {os.path.basename(filepath)} - Modified: {mtime}")
    
    # Run cleanup
    print("\nRunning cleanup_old_recordings()...")
    from main import cleanup_old_recordings
    deleted_count = cleanup_old_recordings()
    print(f"Cleanup returned: {deleted_count} file(s) deleted")
    
    # Verify results
    print("\nVerifying results...")
    old_exists = os.path.exists(old_file)
    new_exists = os.path.exists(new_file)
    
    success = True
    
    if old_exists:
        print(f"  [FAIL] Old file still exists: {old_file}")
        success = False
    else:
        print(f"  [PASS] Old file was deleted")
    
    if not new_exists:
        print(f"  [FAIL] New file was incorrectly deleted")
        success = False
    else:
        print(f"  [PASS] New file was preserved")
        # Clean up new file
        os.remove(new_file)
    
    # Cleanup any remaining test files
    for label, filepath in test_files:
        if os.path.exists(filepath):
            os.remove(filepath)
    
    print("\n" + "=" * 40)
    if success:
        print("TEST PASSED: Cleanup logic works correctly!")
    else:
        print("TEST FAILED: Check logs for details.")
    print("=" * 40)
    
    return success

if __name__ == "__main__":
    test_cleanup()
