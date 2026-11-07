from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class APIResponse(BaseModel):
    success: bool
    message: str

class ModelType(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UploadType(BaseModel):
    id: str
    original_name: str
    stored_filename: str
    path: str
    mime_type: str
    size: int
class UploadFileResponse(APIResponse):
    data: list[UploadType]