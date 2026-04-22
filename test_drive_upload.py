import os
import logging
from google_drive_uploader import GoogleDriveUploader

# Configure logging to console
logging.basicConfig(level=logging.INFO)

def test_upload():
    print("--- Starting Google Drive Upload Test ---")
    
    uploader = GoogleDriveUploader()
    
    print("1. Authenticating...")
    if not uploader.authenticate():
        print("ERROR: Authentication failed!")
        return
    print("Authentication successful.")
    
    # Create a dummy file
    filename = "test_upload_file.txt"
    with open(filename, "w") as f:
        f.write("This is a test file for Google Drive upload.")
    
    print(f"2. Uploading {filename}...")
    link = uploader.upload_file(filename)
    
    if link:
        print(f"SUCCESS: File uploaded! Link: {link}")
    else:
        print("ERROR: Upload failed.")
    
    # Clean up
    if os.path.exists(filename):
        os.remove(filename)
    print("--- Test Finished ---")

if __name__ == "__main__":
    test_upload()
