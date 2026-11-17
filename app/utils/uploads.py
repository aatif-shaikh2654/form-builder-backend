from fastapi import UploadFile
from uuid import uuid4
from pathlib import Path
from app.core.r2 import r2_client
from app.core.config import R2_BUCKET_NAME


async def save_upload_file(file: UploadFile):

    file_id = str(uuid4())

    extension = Path(file.filename or "").suffix

    stored_filename = f"{file_id}{extension}"

    storage_key = f"uploads/{stored_filename}"

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    r2_client.upload_fileobj(
        file.file,
        R2_BUCKET_NAME,
        storage_key,
                ExtraArgs={
            "ContentType": file.content_type or "application/octet-stream"
        },
    )

    await file.close()

    return {
        "id": file_id,
        "original_name": file.filename,
        "stored_filename": stored_filename,
        "storage_key": storage_key,
        "mime_type": file.content_type,
        "size": file_size
    }