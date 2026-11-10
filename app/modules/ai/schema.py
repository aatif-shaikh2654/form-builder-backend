from pydantic import BaseModel, Field
from app.common.schema import APIResponse

from pydantic import BaseModel, Field
from app.modules.forms.models import ConditionActions, ConditionOperator

# AI Schema form


from pydantic import BaseModel, Field, ConfigDict
from typing import Any

from app.modules.forms.models import (
    FormType,
    FieldType,
    LayoutType,
    ConditionOperator,
    ConditionActions,
)


class AIFieldConditionSchema(BaseModel):
    source_field_key: str
    target_field_key: str

    condition_operator: ConditionOperator
    condition_value: dict[str, Any] = Field(default_factory=dict)
    action: ConditionActions


class AIFieldScoringSchema(BaseModel):
    points: float = 1
    allow_partial_credit: bool = False


class AIFieldAnswerKeySchema(BaseModel):
    correct_answer: dict[str, Any]
    explanation: str | None = None


class AIFieldSchema(BaseModel):
    id: str
    field_key: str

    label: str
    description: str | None = None
    field_type: FieldType
    placeholder: str | None = None

    is_required: bool = False
    is_multiple: bool = False

    values: list[str] = Field(default_factory=list)
    position: int = 0

    validation_rules: dict[str, Any] = Field(default_factory=dict)
    default_values: dict[str, Any] = Field(default_factory=dict)
    settings: dict[str, Any] = Field(default_factory=dict)

    conditions: list[AIFieldConditionSchema] = Field(
        default_factory=list
    )

    field_scoring: AIFieldScoringSchema | None = None
    field_answer_key: AIFieldAnswerKeySchema | None = None


class AISectionSchema(BaseModel):
    id: str
    title: str
    description: str | None = None

    position: int = 0

    layout_type: LayoutType = LayoutType.SINGLE_COLUMN
    column_count: int = 1
    layout_config: dict[str, Any] = Field(default_factory=dict)

    is_visible: bool = True

    fields: list[AIFieldSchema] = Field(
        default_factory=list
    )


class AIFormSettingsSchema(BaseModel):
    confirmation_message: str | None = None

    allow_multiple_submission: bool = False
    require_login: bool = False
    show_progress_bar: bool = True
    shuffle_questions: bool = False

    submission_limit: int | None = None

    start_at: str | None = None
    end_at: str | None = None


class AIQuizSettingsSchema(BaseModel):
    time_limit: int | None = None

    passing_score: float = 0

    total_attempts: int | None = None

    show_correct_answers: bool = False
    show_score_after_submissions: bool = True


class AIFormSchema(BaseModel):
    title: str
    description: str | None = None

    form_type: FormType = FormType.FORM

    form_settings: AIFormSettingsSchema = Field(
        default_factory=AIFormSettingsSchema
    )

    quiz_settings: AIQuizSettingsSchema | None = None

    sections: list[AISectionSchema] = Field(
        default_factory=list
    )

    fields: list[AIFieldSchema] = Field(
        default_factory=list
    )

# Generate form payload
class GenerateFormPayload(BaseModel):
    user_prompt: str = Field(
        min_length=2,
        max_length=5000,
    )

class GenerateFormResponse(APIResponse):
    data: dict