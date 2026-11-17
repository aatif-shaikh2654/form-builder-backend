from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from pathlib import Path
from io import BytesIO
from app.core.r2 import r2_client
from app.core.config import R2_BUCKET_NAME
from starlette.concurrency import run_in_threadpool
from app.modules.form_versioning.models import UploadFile as UploadFileModel


async def save_upload_file(
    file: UploadFile,
    db: AsyncSession
):
    storage_key = None

    try:
        # Read uploaded file
        file_content = await file.read()
        file_size = len(file_content)

        extension = Path(file.filename or "").suffix
        stored_filename = f"{uuid4()}{extension}"

        storage_key = f"uploads/{stored_filename}"

        # Create a new readable stream
        file_stream = BytesIO(file_content)

        # Upload to R2
        await run_in_threadpool(
            r2_client.upload_fileobj,
            file_stream,
            R2_BUCKET_NAME,
            storage_key,
            ExtraArgs={
                "ContentType": file.content_type or "application/octet-stream"
            },
        )

        # Save metadata
        upload_file = UploadFileModel(
            original_filename=file.filename or stored_filename,
            storage_key=storage_key,
            mime_type=file.content_type or "application/octet-stream",
            size=file_size,
        )

        db.add(upload_file)

        await db.commit()
        await db.refresh(upload_file)

        return {
                "id": upload_file.id,
                "original_name": upload_file.original_filename,
                "stored_filename": stored_filename,
                "mime_type": upload_file.mime_type,
                "size": file_size
            }

    except Exception:
        await db.rollback()

        if storage_key:
            await run_in_threadpool(
                r2_client.delete_object,
                Bucket=R2_BUCKET_NAME,
                Key=storage_key,
            )

        raise

    finally:
        await file.close()

    


   