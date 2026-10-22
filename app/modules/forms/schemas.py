from pydantic import BaseModel
from app.common.schema import APIResponse, ModelType
from app.modules.forms.models import FieldType, FormStatus, FormType
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class FormResponse(ModelType):
    owner_id: UUID | None
    guest_session_id: UUID | None
    title: str
    description: str | None
    form_type: FormType
    status: FormStatus
    slug: str | None
    published_at: datetime | None

class FormSettingsType(BaseModel):
    confirmation_message: str | None
    allow_multiple_submission: bool
    require_login: bool
    show_progress_bar: bool
    shuffle_questions: bool
    submission_limit: int | None
    start_at: datetime | None
    end_at: datetime | None

class FormSettingsResponse(ModelType, FormSettingsType):
    form_id: UUID


class QuizSettingsType(BaseModel):
    time_limit:int | None
    passing_score: Decimal
    total_attempts:int | None
    show_correct_answers :bool
    show_score_after_submissions:bool

class QuizSettingsResponse(ModelType, QuizSettingsType):
    form_id: UUID

class SectionsType(BaseModel):
    title: str
    description: str | None
    position: int

class FieldsType(BaseModel):
    form_id: UUID | None
    section_id: UUID | None
    label: str
    description: str | None
    field_type: FieldType
    placeholder: str | None
    is_required: bool
    position: int
    validation_rules: dict
    default_values: dict
    settings: dict

class FieldsResponse(ModelType, FieldsType):
    pass

class SectionResponse(ModelType, SectionsType):
    form_id: UUID
    fields: list[FieldsResponse]

# Create form Types    
class CreateFormPayload(BaseModel):
    title: str
    description: str
    form_type: FormType

class CreateFormResponse(APIResponse):
    data: FormResponse


# Edit form types
class EditFormPayload(BaseModel):
    title: str | None
    description: str | None
    form_type: FormType | None
    status: FormStatus | None

class EditFormResponse(APIResponse):
    data: EditFormPayload


# Get all forms type
class GetAllFormsResponse(APIResponse):
    data: list[FormResponse]

# Get signle form type
class SingleForm(FormResponse):
    form_settings: FormSettingsResponse
    quiz_settings: QuizSettingsResponse
    sections: list[SectionResponse]
    fields: list[FieldsResponse]


class GetSingleFormResponse(APIResponse):
    data: SingleForm

# Update form settings types
class UpdateSettingsPayload(FormSettingsType):
    pass

class UpdateSettingsResponse(APIResponse):
    data: FormSettingsResponse

# Update quiz settings types
class UpdateQuizSettingsPayload(QuizSettingsType):
    pass

class UpdateQuizSettingsResponse(APIResponse):
    data: QuizSettingsResponse

# Form Section types
class AddSectionPayload(SectionsType):
    pass

class EditSectionPayload(BaseModel):
    title: str | None
    description: str | None
    position: int | None

class AddEditSectionResponse(APIResponse):
    data: SectionResponse

# Form Fields types
class AddFieldPayload(FieldsType):
    pass

class EditFieldPayload(BaseModel):
    form_id: UUID | None
    section_id: UUID | None
    label: str | None
    description: str | None
    field_type: FieldType | None
    placeholder: str | None
    is_required: bool | None
    position: int | None
    validation_rules: dict | None
    default_values: dict | None
    settings: dict | None

class AddEditFieldResponse(APIResponse):
    data: FieldsResponse