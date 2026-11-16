import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_to_shared_drive():
    key_json_str = os.environ.get('GDRIVE_CREDENTIALS')
    folder_id = os.environ.get('GDRIVE_FOLDER_ID')
    file_path = os.environ.get('GDRIVE_FILE_PATH')
    file_name = os.environ.get('GDRIVE_FILE_NAME')

    if not key_json_str:
        raise ValueError("GDRIVE_CREDENTIALS não encontrado.")
    if not folder_id:
        raise ValueError("GDRIVE_FOLDER_ID não encontrado.")
    if not file_path or not os.path.isfile(file_path):
        raise FileNotFoundError(f"APK não encontrado: {file_path!r}")
    if not file_name:
        raise ValueError("GDRIVE_FILE_NAME não encontrado.")

    info = json.loads(key_json_str)
    SCOPES = ['https://www.googleapis.com/auth/drive']
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': file_name,
        'parents': [folder_id],
    }
    media = MediaFileUpload(
        file_path,
        mimetype='application/vnd.android.package-archive',
        resumable=True,
    )

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id',
        supportsAllDrives=True,
    ).execute()

    print(f"APK enviado. ID: {file.get('id')}")

if __name__ == '__main__':
    upload_to_shared_drive()