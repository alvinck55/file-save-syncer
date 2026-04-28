from __future__ import annotations

import importlib.resources as pkg_resources
import json
import os

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from windrose.config.paths import TOKEN_FILE

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


class AuthError(Exception):
    pass


def load_credentials() -> Credentials:
    if not TOKEN_FILE.exists():
        raise AuthError("Not authenticated. Run `windrose init` first.")

    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds)
        except RefreshError as e:
            raise AuthError(f"Auth token expired and could not be refreshed: {e}") from e

    return creds


def run_oauth_flow() -> Credentials:
    flow = InstalledAppFlow.from_client_config(_load_client_config(), SCOPES)
    creds = flow.run_local_server(port=8080, open_browser=True)
    _save_token(creds)
    return creds


def build_service():
    creds = load_credentials()
    return build("drive", "v3", credentials=creds)


def _load_client_config() -> dict:
    data = pkg_resources.files("windrose.data").joinpath("client_secret.json").read_text()
    return json.loads(data)


def _save_token(creds: Credentials) -> None:
    TOKEN_FILE.write_text(creds.to_json())
    if os.name != "nt":
        TOKEN_FILE.chmod(0o600)
