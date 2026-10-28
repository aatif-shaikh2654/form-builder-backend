from fastapi import APIRouter, Request
from app.db.session import DbSession
from app.modules.forms.schemas import (CreateFormPayload, CreateFormResponse, EditFormPayload,
    EditFormResponse, GetAllFormsResponse, GetSingleFormResponse, PublishFormResponse,
    SaveFormPayload, SaveFormResponse, SubmissionPayload, UpdateQuizSettingsPayload,
    UpdateQuizSettingsResponse, UpdateSettingsPayload, UpdateSettingsResponse)
from app.core.dependencies import GetGuestSession
from app.modules.forms.service import (
    create_form_service, 
    edit_form_service, 
    get_all_forms_service, 
    get_single_form_service, 
    update_form_settings_service, 
    update_quiz_settings_service, 
    delete_form_service, 
    delete_form_service,
    publish_form_service,
    save_draft_form_service,
    submit_form_service
)
from app.common.schema import APIResponse
from app.modules.forms.models import FormType


router = APIRouter(prefix="/form", tags=["Forms"])


@router.post("/create", response_model=CreateFormResponse)
async def create_form(payload: CreateFormPayload, session: GetGuestSession, db: DbSession):
    
    response = await create_form_service(payload, session, db)

    return {
        "success": True,
        "message": "Form successfully created",
        "data": response
    }

@router.patch("/{form_id}", response_model=EditFormResponse)
async def edit_form(form_id: str, payload: EditFormPayload, session: GetGuestSession, db: DbSession):

    response = await edit_form_service(form_id, payload, session, db)

    return {
        "success": True,
        "message": "Form edited successfully",
        "data": response
    }

@router.get("/all", response_model=GetAllFormsResponse)
async def get_all_forms(session: GetGuestSession, db: DbSession, page: int | None, limit: int | None, form_type: FormType | None = None, search: str | None = None):

    query = {
        "page": page,
        "limit": limit,
        "form_type": form_type,
        "search": search,
    }
    response = await get_all_forms_service(query, session=session, db=db)

    return {
        "success": True,
        "message": "Forms fetched successfully",
        "data": response
    }

@router.get("/{form_id}", response_model=GetSingleFormResponse)
async def get_single_form(form_id: str, session: GetGuestSession, db: DbSession):

    response = await get_single_form_service(form_id, session, db)
    
    return {
        "success": True,
        "message": "Form fetched successfully",
        "data": response
    }

@router.delete("/{form_id}", response_model=APIResponse)
async def delete_form(form_id: str, session: GetGuestSession, db: DbSession):

    await delete_form_service(form_id, session, db)
    
    return {
        "success": True,
        "message": "Form deleted successfully",
    }

@router.patch("/{form_id}/settings", response_model=UpdateSettingsResponse)
async def update_settings(form_id: str, payload: UpdateSettingsPayload, session: GetGuestSession, db: DbSession):

    response = await update_form_settings_service(form_id, payload, session, db)

    return {
        "success": True,
        "message": "Setting updated successfully",
        "data": response
    }

@router.patch("/{form_id}/quiz-settings", response_model=UpdateQuizSettingsResponse)
async def update_quiz_settings(form_id: str, payload: UpdateQuizSettingsPayload, session: GetGuestSession, db: DbSession):
    
    response = await update_quiz_settings_service(form_id, payload, session, db)

    return {
        "success": True,
        "message": "Quiz Setting updated successfully",
        "data": response
    }

@router.post("/{form_id}/publish", response_model=PublishFormResponse)
async def publish_form(form_id: str, session: GetGuestSession, db: DbSession):

    response = await publish_form_service(form_id, session, db)

    return {
        "success": True,
        "message": "Form published successfully",
        "data": response
    }

@router.put("/{form_id}/save-draft", response_model=SaveFormResponse)
async def save_draft_form(form_id: str, payload: SaveFormPayload, session: GetGuestSession, db: DbSession):

    response = await save_draft_form_service(form_id, payload, session, db)

    return {
        "success": True,
        "message": "Form saved successfully",
        "data": response
    }


@router.post("/{form_id}/submit", response_model=APIResponse)
async def submit_form(form_id: str, payload: SubmissionPayload, session: GetGuestSession, db: DbSession):

    await submit_form_service(form_id, payload, session, db)

    return {
        "success": True,
        "message": "form submitted successfully"
    }