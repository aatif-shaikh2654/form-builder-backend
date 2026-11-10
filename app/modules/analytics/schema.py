from pydantic import BaseModel
from app.common.schema import APIResponse, ModelType
from app.modules.form_versioning.schema import AnswerType, SubmissionType
from app.modules.forms.schema import FieldsResponse

class SubmissionAnswerResponse(AnswerType):
    field: FieldsResponse

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