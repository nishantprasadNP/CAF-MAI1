from __future__ import annotations

import os
import json
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = Path(
    os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "googledriveapi_key/caf-mai-355929bea6ba.json")
)
DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1a8U4aAbiRrNxMWhYJGziJb2GZ8dvJLuv").strip()


class DriveUploadError(Exception):
    """Raised when Google Drive upload fails in a client-safe way."""


def _get_service_account_credentials():
    if not SERVICE_ACCOUNT_FILE.exists():
        raise DriveUploadError(
            f"Service account key file not found: {SERVICE_ACCOUNT_FILE}. "
            "Set GOOGLE_SERVICE_ACCOUNT_FILE or place the service account key at this path."
        )

    try:
        key_data = json.loads(SERVICE_ACCOUNT_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        raise DriveUploadError(f"Invalid JSON in service account key file: {exc}") from exc

    if key_data.get("type") != "service_account":
        raise DriveUploadError(
            "Invalid Google credentials file: expected a service account key "
            '(JSON field "type" must be "service_account").'
        )

    try:
        return service_account.Credentials.from_service_account_file(
            str(SERVICE_ACCOUNT_FILE),
            scopes=SCOPES,
        )
    except Exception as exc:
        raise DriveUploadError(f"Failed to load service account credentials: {exc}") from exc


def upload_to_drive(file_path: str, file_name: str) -> str:
    """
    Upload a file to Google Drive and return the uploaded file ID.
    """
    if not Path(file_path).exists():
        raise DriveUploadError(f"File not found for upload: {file_path}")
    if not DRIVE_FOLDER_ID:
        raise DriveUploadError(
            "Google Drive folder ID is missing. "
            "Set GOOGLE_DRIVE_FOLDER_ID or configure DRIVE_FOLDER_ID in code."
        )

    credentials = _get_service_account_credentials()
    service = build("drive", "v3", credentials=credentials)
    print(f"Uploading '{file_name}' to Google Drive folder ID: {DRIVE_FOLDER_ID}")

    # Always upload into the configured shared folder to avoid service-account root uploads.
    file_metadata = {"name": file_name, "parents": [DRIVE_FOLDER_ID]}
    media = MediaFileUpload(file_path, resumable=True)

    try:
        uploaded_file = (
            service.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id",
                supportsAllDrives=True,
            )
            .execute()
        )
    except HttpError as exc:
        if exc.resp is not None and exc.resp.status == 403:
            raise DriveUploadError(
                "Google Drive permission/quota error. Verify the folder is shared with the "
                "service account and preferably located in a Shared Drive."
            ) from exc
        raise DriveUploadError(f"Google Drive API error: {exc}") from exc
    except Exception as exc:
        raise DriveUploadError(f"Unexpected Drive upload error: {exc}") from exc

    file_id = uploaded_file.get("id")
    if not file_id:
        raise DriveUploadError("Upload succeeded but no Google Drive file ID was returned.")

    return file_id
