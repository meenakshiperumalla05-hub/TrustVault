
import hashlib
import io
import zipfile

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status


MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".txt",
    ".png",
    ".jpg",
}

SIGNATURES = {
    ".pdf": lambda data: data.startswith(b"%PDF-"),
    ".png": lambda data: data.startswith(b"\x89PNG\r\n\x1a\n"),
    ".jpg": lambda data: data.startswith(b"\xff\xd8\xff"),
}


def validate_file_content(data: bytes, extension: str) -> None:
    if extension in SIGNATURES:
        if not SIGNATURES[extension](data):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not match its extension",
            )
        return

    if extension in {".docx", ".xlsx"}:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                names = set(archive.namelist())

                if extension == ".docx":
                    valid = (
                        "[Content_Types].xml" in names
                        and "word/document.xml" in names
                    )
                else:
                    valid = (
                        "[Content_Types].xml" in names
                        and "xl/workbook.xml" in names
                    )

                if not valid:
                    raise ValueError("Invalid Office document structure")

        except (zipfile.BadZipFile, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Office document",
            )

        return

    if extension == ".txt":
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text file must use UTF-8 encoding",
            )


def inspect_upload(filename: str, data: bytes) -> tuple[str, str]:
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type is not allowed",
        )

    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty files are not allowed",
        )

    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Maximum file size is 10 MB",
        )

    validate_file_content(data, extension)

    content_types = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".txt": "text/plain",
        ".png": "image/png",
        ".jpg": "image/jpeg",
    }

    return extension, content_types[extension]


async def save_upload(upload: UploadFile, storage_path: str):
    data = await upload.read(MAX_FILE_SIZE + 1)

    extension, content_type = inspect_upload(
        upload.filename or "",
        data,
    )

    storage_dir = Path(storage_path).resolve()
    storage_dir.mkdir(parents=True, exist_ok=True)

    stored_name = f"{uuid4().hex}{extension}"
    destination = storage_dir / stored_name

    destination.write_bytes(data)

    file_hash = hashlib.sha256(data).hexdigest()

    return {
        "file_path": str(destination),
        "stored_name": stored_name,
        "content_type": content_type,
        "file_size": len(data),
        "file_hash": file_hash,
    }
