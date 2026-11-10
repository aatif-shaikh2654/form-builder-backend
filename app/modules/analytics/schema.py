from pydantic import BaseModel
from app.common.schema import APIResponse, ModelType
from app.modules.form_versioning.schema import AnswerType, SubmissionType
from app.modules.forms.schema import FieldsType

# Field without conditions: submissions don't need them, and loading them would require eager-loading conditions_as_source
class SubmissionFieldResponse(ModelType, FieldsType):
    pass

class SubmissionAnswerResponse(AnswerType):
    field: SubmissionFieldResponse

class SubmissionResponse(SubmissionType, ModelType):
    submission_answers: list[SubmissionAnswerResponse]

class FormAnalyticsResponse(BaseModel):
    items: list[SubmissionResponse]
    page: int | None
    limit: int | None
    total: int | None
    total_pages: int | None

class FormAnalyticsQueryResponse(APIResponse):
    data: FormAnalyticsResponse