from __future__ import annotations

import io
import os
import uuid
from pathlib import Path

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload


class DriveClient:
    def __init__(self, service) -> None:
        self._svc = service

    def create_folder(self, name: str) -> str:
        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        folder = self._svc.files().create(body=metadata, fields="id").execute()
        return folder["id"]

    def upload_file(
        self,
        local_path: Path,
        folder_id: str,
        drive_filename: str,
        existing_file_id: str | None = None,
    ) -> str:
        from googleapiclient.http import MediaIoBaseUpload
        with open(local_path, "rb") as f:
            data = f.read()
        media = MediaIoBaseUpload(io.BytesIO(data), mimetype="application/octet-stream", resumable=True)
        if existing_file_id:
            result = (
                self._svc.files()
                .update(fileId=existing_file_id, media_body=media, fields="id")
                .execute()
            )
        else:
            metadata = {"name": drive_filename, "parents": [folder_id]}
            result = (
                self._svc.files()
                .create(body=metadata, media_body=media, fields="id")
                .execute()
            )
        return result["id"]

    def download_file(self, file_id: str, dest_path: Path) -> None:
        request = self._svc.files().get_media(fileId=file_id)
        tmp = dest_path.parent / f".alvault-dl-{uuid.uuid4().hex}.tmp"
        try:
            with io.FileIO(str(tmp), "wb") as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
            os.replace(tmp, dest_path)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise

    def get_file_metadata(self, file_id: str) -> dict:
        return (
            self._svc.files()
            .get(fileId=file_id, fields="id,name,modifiedTime")
            .execute()
        )

    def get_folder_metadata(self, folder_id: str) -> dict:
        return (
            self._svc.files()
            .get(fileId=folder_id, fields="id,name")
            .execute()
        )

    def upload_bytes(self, folder_id: str, filename: str, data: bytes, existing_file_id: str | None = None) -> str:
        from googleapiclient.http import MediaIoBaseUpload
        media = MediaIoBaseUpload(io.BytesIO(data), mimetype="application/octet-stream")
        if existing_file_id:
            result = (
                self._svc.files()
                .update(fileId=existing_file_id, media_body=media, fields="id")
                .execute()
            )
        else:
            metadata = {"name": filename, "parents": [folder_id]}
            result = self._svc.files().create(body=metadata, media_body=media, fields="id").execute()
        return result["id"]

    def download_bytes(self, file_id: str) -> bytes:
        request = self._svc.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return fh.getvalue()

    def delete_file(self, file_id: str) -> None:
        self._svc.files().delete(fileId=file_id).execute()

    def find_file_in_folder(self, filename: str, folder_id: str) -> str | None:
        query = (
            f"name='{filename}' and '{folder_id}' in parents and trashed=false"
        )
        results = self._svc.files().list(q=query, fields="files(id)").execute()
        files = results.get("files", [])
        return files[0]["id"] if files else None

    def invite_user(self, folder_id: str, email: str) -> None:
        self._svc.permissions().create(
            fileId=folder_id,
            body={"type": "user", "role": "writer", "emailAddress": email},
            sendNotificationEmail=True,
            emailMessage="You've been invited to join a shared world via alvault. Run `alvault join` with the folder ID to get started.",
            fields="id",
        ).execute()
