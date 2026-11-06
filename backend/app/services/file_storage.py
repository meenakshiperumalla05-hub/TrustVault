import hashlib
import io
import uuid
import zipfile
from pathlib import Path
from urllib.parse import quote

import httpx
from fastapi import HTTPException, UploadFile

from app.config import settings


MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".txt",
    ".png",
    ".jpg",
    ".jpeg",
}

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
    "image/png",
    "image/jpeg",
}


def _supabase_configured():
    return bool(
        settings.supabase_url
        and settings.supabase_service_role_key
        and settings.supabase_bucket
    )


def _supabase_headers(content_type=None):
    headers = {
        "apikey": settings.supabase_service_role_key,
    }

    if content_type:
        headers["Content-Type"] = content_type

    return headers


def _validate_file(filename, content_type, file_bytes):
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="File type not allowed.",
        )

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file content type.",
        )

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Empty files are not allowed.",
        )

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds the 10 MB limit.",
        )

    # Validate file signatures and basic file structure.
    if extension == ".pdf":
        if not file_bytes.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file.",
            )

    elif extension == ".png":
        if not file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            raise HTTPException(
                status_code=400,
                detail="Invalid PNG file.",
            )

    elif extension in {".jpg", ".jpeg"}:
        if not file_bytes.startswith(b"\xff\xd8\xff"):
            raise HTTPException(
                status_code=400,
                detail="Invalid JPEG file.",
            )

    elif extension in {".docx", ".xlsx"}:
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
                file_names = archive.namelist()

                if extension == ".docx":
                    valid = (
                        "[Content_Types].xml" in file_names
                        and "word/document.xml" in file_names
                    )
                else:
                    valid = (
                        "[Content_Types].xml" in file_names
                        and "xl/workbook.xml" in file_names
                    )

                if not valid:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid Office document.",
                    )

        except zipfile.BadZipFile:
            raise HTTPException(
                status_code=400,
                detail="Invalid Office document.",
            )

    elif extension == ".txt":
        try:
            file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Text file must use UTF-8 encoding.",
            )


async def save_upload(file: UploadFile, storage_path: str):
    original_filename = Path(file.filename or "upload").name
    content_type = file.content_type or "application/octet-stream"

    file_bytes = await file.read()

    _validate_file(
        original_filename,
        content_type,
        file_bytes,
    )

    file_hash = hashlib.sha256(file_bytes).hexdigest()
    extension = Path(original_filename).suffix.lower()
    stored_filename = f"{uuid.uuid4().hex}{extension}"

    # Supabase private bucket storage.
    if _supabase_configured():
        object_path = stored_filename

        url = (
            f"{settings.supabase_url.rstrip('/')}"
            f"/storage/v1/object/"
            f"{quote(settings.supabase_bucket, safe='')}/"
            f"{quote(object_path, safe='/')}"
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    headers={
                        **_supabase_headers(content_type),
                        "x-upsert": "false",
                    },
                    content=file_bytes,
                )

                response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Supabase upload failed: "
                    f"{exc.response.text[:500]}"
                ),
            )

        except httpx.RequestError:
            raise HTTPException(
                status_code=502,
                detail="Unable to connect to Supabase Storage.",
            )

        return {
            "file_path": object_path,
            "file_size": len(file_bytes),
            "file_hash": file_hash,
            "content_type": content_type,
            "original_filename": original_filename,
            "storage": "supabase",
        }

    # Local storage fallback for development.
    local_directory = Path(storage_path)
    local_directory.mkdir(parents=True, exist_ok=True)

    local_file = local_directory / stored_filename
    local_file.write_bytes(file_bytes)

    return {
        "file_path": str(local_file),
        "file_size": len(file_bytes),
        "file_hash": file_hash,
        "content_type": content_type,
        "original_filename": original_filename,
        "storage": "local",
    }


async def read_stored_file(file_path: str) -> bytes:
    if _supabase_configured():
        object_path = file_path.lstrip("/")

        url = (
            f"{settings.supabase_url.rstrip('/')}"
            f"/storage/v1/object/"
            f"{quote(settings.supabase_bucket, safe='')}/"
            f"{quote(object_path, safe='/')}"
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    url,
                    headers=_supabase_headers(),
                )

                response.raise_for_status()
                return response.content

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail="Stored file not found.",
                )

            raise HTTPException(
                status_code=502,
                detail="Unable to download file from Supabase Storage.",
            )

        except httpx.RequestError:
            raise HTTPException(
                status_code=502,
                detail="Unable to connect to Supabase Storage.",
            )

    local_file = Path(file_path)

    if not local_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="Stored file not found.",
        )

    return local_file.read_bytes()


async def delete_stored_file(file_path: str):
    if not file_path:
        return

    if _supabase_configured():
        object_path = file_path.lstrip("/")

        url = (
            f"{settings.supabase_url.rstrip('/')}"
            f"/storage/v1/object/"
            f"{quote(settings.supabase_bucket, safe='')}"
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.request(
    "DELETE",
                    url,
                    headers=_supabase_headers(
                        "application/json"
                    ),
                    json={
                        "prefixes": [object_path],
                    },
                )

                response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=502,
                detail="Unable to delete file from Supabase Storage.",
            )

        except httpx.RequestError:
            raise HTTPException(
                status_code=502,
                detail="Unable to connect to Supabase Storage.",
            )

        return

    local_file = Path(file_path)
    local_file.unlink(missing_ok=True)