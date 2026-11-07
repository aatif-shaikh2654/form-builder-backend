from pydantic import BaseModel
from app.common.schema import APIResponse, ModelType
from app.modules.forms.models import FieldType, FormStatus, FormType, LayoutType
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
    current_published_version_id: UUID | None
    published_version: int | None
    draft_version: int | None

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



class FieldsType(BaseModel):
    form_id: UUID | None
    section_id: UUID | None
    label: str
    description: str | None
    field_type: FieldType
    placeholder: str | None
    is_required: bool
    is_multiple: bool | None
    values: list[str] | None = None
    position: int
    validation_rules: dict
    default_values: dict
    settings: dict

class FieldsResponse(ModelType, FieldsType):
    pass

class SectionsType(BaseModel):
    title: str
    description: str | None = None
    position: int = 0
    layout_type: LayoutType = LayoutType.SINGLE_COLUMN
    column_count: int = 1
    layout_config: dict = {}
    is_visible: bool = True
    fields: list[FieldsResponse] = []

class SectionResponse(ModelType, SectionsType):
    form_id: UUID
    fields: list[FieldsResponse] = []

# Create form Types    
class CreateFormPayload(BaseModel):
    title: str
    description: str
    form_type: FormType

class CreateFormResponse(APIResponse):
    data: FormResponse


# Edit form types
class EditFormPayload(FormSettingsType):
    title: str | None
    description: str | None
    form_type: FormType | None
    status: FormStatus | None

class EditFormResponse(APIResponse):
    data: FormResponse


# Get all forms type
class StatsResponse(BaseModel): 
    total_forms: int | None
    published: int | None
    drafts: int | None
    quizes: int | None
class GetAllFormQueryResponse(BaseModel):
    items: list[FormResponse]
    stats: StatsResponse
    page: int | None
    limit: int | None
    total: int | None
    total_pages: int | None

class GetAllFormsResponse(APIResponse):
    data: GetAllFormQueryResponse

# Get signle form type
class SingleForm(FormResponse):
    form_settings: FormSettingsResponse | None
    quiz_settings: QuizSettingsResponse | None
    sections: list[SectionResponse]
    fields: list[FieldsResponse]


class GetSingleFormResponse(APIResponse):
    data: SingleForm

# Update quiz settings types
class UpdateQuizSettingsPayload(QuizSettingsType):
    pass

class UpdateQuizSettingsResponse(APIResponse):
    data: QuizSettingsResponse

