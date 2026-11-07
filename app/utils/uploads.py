from fastapi import UploadFile
from uuid import uuid4
from pathlib import Path


async def save_upload_file(file: UploadFile, path: str):

    UPLOAD_DIR = Path(path)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    file_id = str(uuid4())

    extension = Path(file.filename or "").suffix

    stored_filename = f"{file_id}{extension}"

    file_path = UPLOAD_DIR / stored_filename

    size = 0

    with file_path.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            buffer.write(chunk)

    await file.close()

    return {
        "id": file_id,
        "original_name": file.filename,
        "stored_filename": stored_filename,
        "path": str(file_path),
        "mime_type": file.content_type,
        "size": size
    }