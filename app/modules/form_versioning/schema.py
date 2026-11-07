# Publish form type
from app.common.schema import APIResponse, ModelType
from app.modules.forms.schemas import (FieldsResponse, FieldsType, FormResponse, SectionResponse,
    SectionsType, SingleForm)
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from app.modules.form_versioning.models import SubmissionStatus
# Save form types
class SaveFormPayload(BaseModel):
    title: str | None
    description: str | None
    sections: list[dict] | list[SectionResponse] | list[SectionsType] = []
    fields: list[dict] | list[FieldsResponse] | list[FieldsType] = []

class SaveFormResponse(APIResponse):
    data: SingleForm

# Publish form types
class PublishFormResponse(APIResponse):
    data: FormResponse

# Get draft form
class DraftFormType(ModelType):
    form_id: UUID
    version_number: int
    content: dict
    published_at: datetime | None
    published_by_id: UUID | None

class DraftFormResponse(APIResponse):
    data: DraftFormType

# Get published form
class GetPublishedFormResponse(APIResponse):
    data: DraftFormType

# User Form submission
class SubmissionType(ModelType):
    form_id: UUID
    respondent_id: UUID | None
    response_number: int | None
    status: SubmissionStatus
    started_at: datetime | None
    submitted_at: datetime | None
    respondent_metadata: dict

class AnswerResponse(BaseModel):
    field_id: UUID
    answer_text: str | None
    answer_json: dict | list | None

class AnswerType(ModelType, AnswerResponse):
    pass
class SubmissionPayload(BaseModel):
    respondent_metadata: dict
    answers: list[AnswerResponse]
    