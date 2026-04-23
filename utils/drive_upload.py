from __future__ import annotations

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]
OAUTH_TOKEN_FILE = Path(
    os.getenv("GOOGLE_OAUTH_TOKEN_FILE", "googledriveapi_key/oauth_token.json")
)
DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1a8U4aAbiRrNxMWhYJGziJb2GZ8dvJLuv").strip()


class DriveUploadError(Exception):
    """Raised when Google Drive upload fails in a client-safe way."""


def _get_user_credentials():
    if not OAUTH_TOKEN_FILE.exists():
        raise DriveUploadError(
            f"OAuth token file not found: {OAUTH_TOKEN_FILE}. "
            "Run `python scripts/init_drive_oauth.py` once to authorize your Google account."
        )

    try:
        credentials = Credentials.from_authorized_user_file(str(OAUTH_TOKEN_FILE), SCOPES)
    except Exception as exc:
        raise DriveUploadError(f"Invalid OAuth token file: {exc}") from exc

    if credentials.valid:
        return credentials

    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            OAUTH_TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
            return credentials
        except Exception as exc:
            raise DriveUploadError(
                "OAuth token refresh failed. Run `python scripts/init_drive_oauth.py` to re-authorize."
            ) from exc

    raise DriveUploadError(
        "OAuth token is invalid. Run `python scripts/init_drive_oauth.py` to re-authorize."
    )


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

    credentials = _get_user_credentials()
    service = build("drive", "v3", credentials=credentials)
    print(f"Uploading '{file_name}' to Google Drive folder ID: {DRIVE_FOLDER_ID}")

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
                "Google Drive permission/quota error for the authorized OAuth user."
            ) from exc
        raise DriveUploadError(f"Google Drive API error: {exc}") from exc
    except Exception as exc:
        raise DriveUploadError(f"Unexpected Drive upload error: {exc}") from exc

    file_id = uploaded_file.get("id")
    if not file_id:
        raise DriveUploadError("Upload succeeded but no Google Drive file ID was returned.")

    return file_id
