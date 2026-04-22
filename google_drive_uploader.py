import os
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config import BASE_DIR, GOOGLE_DRIVE_FOLDER_NAME, CLIENT_SECRETS_PATH

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveUploader:
    def __init__(self):
        self.creds = None
        self.service = None
        self.token_path = os.path.join(BASE_DIR, 'token.json')
        self.folder_id = None

    def authenticate(self):
        """Authenticates the user using OAuth2."""
        try:
            if os.path.exists(self.token_path):
                self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            
            # If there are no (valid) credentials available, let the user log in.
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    try:
                        self.creds.refresh(Request())
                    except Exception as refresh_err:
                        logging.warning(f"Failed to refresh token (might be revoked): {refresh_err}")
                        logging.info("Deleting invalid token and restarting authentication...")
                        self.creds = None # Reset creds
                        if os.path.exists(self.token_path):
                            try:
                                os.remove(self.token_path)
                            except:
                                pass
                
                if not self.creds:
                    if not os.path.exists(CLIENT_SECRETS_PATH):
                        logging.error(f"Client secrets file not found at {CLIENT_SECRETS_PATH}")
                        return False
                        
                    flow = InstalledAppFlow.from_client_secrets_file(
                        CLIENT_SECRETS_PATH, SCOPES)
                    self.creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(self.token_path, 'w') as token:
                    token.write(self.creds.to_json())

            self.service = build('drive', 'v3', credentials=self.creds)
            logging.info("Google Drive authentication successful.")
            return True
        except Exception as e:
            logging.error(f"Google Drive authentication failed: {e}", exc_info=True)
            return False

    def _get_folder_id(self, folder_name):
        """Finds or creates the target folder."""
        if self.folder_id:
            return self.folder_id

        try:
            # Search for the folder
            query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
            results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            items = results.get('files', [])

            if not items:
                # Create the folder
                file_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                file = self.service.files().create(body=file_metadata, fields='id').execute()
                self.folder_id = file.get('id')
                logging.info(f"Created Google Drive folder: {folder_name} (ID: {self.folder_id})")
            else:
                self.folder_id = items[0]['id']
                logging.info(f"Found existing Google Drive folder: {folder_name} (ID: {self.folder_id})")
            
            return self.folder_id
        except Exception as e:
            logging.error(f"Error getting folder ID: {e}")
            return None

    def upload_file(self, file_path):
        """Uploads a file to the configured Google Drive folder."""
        if not self.service:
            if not self.authenticate():
                return None

        try:
            folder_id = self._get_folder_id(GOOGLE_DRIVE_FOLDER_NAME)
            if not folder_id:
                logging.error("Could not determine destination folder.")
                return None

            file_name = os.path.basename(file_path)
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            media = MediaFileUpload(file_path, resumable=True)

            logging.info(f"Starting upload of {file_name} to Google Drive...")
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
            
            logging.info(f"File uploaded successfully. File ID: {file.get('id')}")
            return file.get('webViewLink')
        except Exception as e:
            logging.error(f"Error uploading file to Google Drive: {e}", exc_info=True)
            return None
