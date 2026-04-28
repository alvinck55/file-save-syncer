from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from windrose.drive.client import DriveClient


def _make_client():
    service = MagicMock()
    return DriveClient(service), service


def test_find_or_create_folder_existing():
    client, svc = _make_client()
    svc.files().list().execute.return_value = {"files": [{"id": "existing_id"}]}

    result = client.find_or_create_folder("windrose-saves")
    assert result == "existing_id"
    svc.files().create.assert_not_called()


def test_find_or_create_folder_new():
    client, svc = _make_client()
    svc.files().list().execute.return_value = {"files": []}
    svc.files().create().execute.return_value = {"id": "new_id"}

    result = client.find_or_create_folder("windrose-saves")
    assert result == "new_id"


def test_upload_file_new(tmp_path):
    client, svc = _make_client()
    svc.files().create().execute.return_value = {"id": "file123"}

    f = tmp_path / "save.zip"
    f.write_bytes(b"data")

    file_id = client.upload_file(f, "folder_id", "save.zip", existing_file_id=None)
    assert file_id == "file123"


def test_upload_file_update(tmp_path):
    client, svc = _make_client()
    svc.files().update().execute.return_value = {"id": "file123"}

    f = tmp_path / "save.zip"
    f.write_bytes(b"data")

    file_id = client.upload_file(f, "folder_id", "save.zip", existing_file_id="file123")
    assert file_id == "file123"


def test_download_file(tmp_path):
    client, svc = _make_client()

    chunk = b"save content"

    def next_chunk_side_effect():
        return None, True

    mock_downloader = MagicMock()
    mock_downloader.next_chunk.side_effect = next_chunk_side_effect

    dest = tmp_path / "save.sav"

    with patch("windrose.drive.client.MediaIoBaseDownload") as mock_dl_cls:
        mock_dl_cls.return_value = mock_downloader
        with patch("windrose.drive.client.io.FileIO") as mock_fio:
            mock_fio.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_fio.return_value.__exit__ = MagicMock(return_value=False)
            with patch("windrose.drive.client.os.replace"):
                client.download_file("file_id", dest)

    svc.files().get_media.assert_called_once_with(fileId="file_id")


def test_invite_user():
    client, svc = _make_client()
    svc.permissions().create().execute.return_value = {"id": "perm123"}

    client.invite_user("folder_id", "friend@gmail.com")

    call_kwargs = svc.permissions().create.call_args.kwargs
    assert call_kwargs["fileId"] == "folder_id"
    assert call_kwargs["body"] == {"type": "user", "role": "writer", "emailAddress": "friend@gmail.com"}
    assert call_kwargs["sendNotificationEmail"] is True
    assert call_kwargs["fields"] == "id"
