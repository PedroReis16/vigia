#!/usr/bin/env python3
"""Upload (or overwrite) a file to a Google Shared Drive folder via service account."""

from __future__ import annotations

import json
import mimetypes
import os
import sys

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"::error::Variável de ambiente obrigatória ausente: {name}")
    return value


def _drive_service(credentials_json: str):
    try:
        info = json.loads(credentials_json)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"::error::GDRIVE_CREDENTIALS não é um JSON válido: {exc}") from exc

    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _find_existing_file(service, folder_id: str, file_name: str) -> str | None:
    # Escape single quotes in Drive query syntax.
    safe_name = file_name.replace("\\", "\\\\").replace("'", "\\'")
    query = (
        f"name = '{safe_name}' and '{folder_id}' in parents and trashed = false"
    )
    response = (
        service.files()
        .list(
            q=query,
            spaces="drive",
            fields="files(id, name)",
            pageSize=10,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora="allDrives",
        )
        .execute()
    )
    files = response.get("files", [])
    if not files:
        return None
    if len(files) > 1:
        print(
            f"::warning::{len(files)} arquivos com nome '{file_name}' na pasta; "
            "atualizando o primeiro."
        )
    return files[0]["id"]


def upload_or_overwrite() -> None:
    credentials_json = _require_env("GDRIVE_CREDENTIALS")
    folder_id = _require_env("GDRIVE_FOLDER_ID")
    file_path = _require_env("GDRIVE_FILE_PATH")
    file_name = os.environ.get("GDRIVE_FILE_NAME", "").strip() or os.path.basename(file_path)

    if not os.path.isfile(file_path):
        raise SystemExit(f"::error::Arquivo local não encontrado: {file_path}")

    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = "application/vnd.android.package-archive"

    service = _drive_service(credentials_json)
    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
    existing_id = _find_existing_file(service, folder_id, file_name)

    if existing_id:
        result = (
            service.files()
            .update(
                fileId=existing_id,
                media_body=media,
                fields="id, name, webViewLink",
                supportsAllDrives=True,
            )
            .execute()
        )
        action = "atualizado"
    else:
        result = (
            service.files()
            .create(
                body={"name": file_name, "parents": [folder_id]},
                media_body=media,
                fields="id, name, webViewLink",
                supportsAllDrives=True,
            )
            .execute()
        )
        action = "criado"

    file_id = result.get("id", "")
    link = result.get("webViewLink") or f"https://drive.google.com/file/d/{file_id}/view"
    print(f"✓ APK {action} no Google Drive: {result.get('name')} (id={file_id})")
    print(f"  {link}")


if __name__ == "__main__":
    try:
        upload_or_overwrite()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — falha da pipeline com mensagem clara
        print(f"::error::Falha no upload para o Google Drive: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
