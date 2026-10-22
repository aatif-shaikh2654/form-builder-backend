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