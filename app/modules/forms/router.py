from fastapi import APIRouter
from app.db.session import DbSession, session
from app.modules.forms.schemas import (AddEditFieldResponse, AddEditSectionResponse,
    AddFieldPayload, AddSectionPayload, CreateFormPayload, CreateFormResponse, EditFieldPayload,
    EditFormPayload, EditFormResponse, EditSectionPayload, GetAllFormsResponse,
    GetSingleFormResponse, UpdateQuizSettingsPayload,
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
    add_section_service, 
    edit_section_service, 
    delete_section_service, 
    add_field_service, 
    edit_field_service, 
    delete_form_service
)
from app.common.schema import APIResponse


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
async def get_all_forms(session: GetGuestSession, db: DbSession):

    response = await get_all_forms_service(session, db)

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

@router.post("/{form_id}/section", response_model=AddEditSectionResponse)
async def add_form_section(form_id: str, payload: AddSectionPayload, session: GetGuestSession, db: DbSession):

    response = await add_section_service(form_id, payload, session, db)

    return {
        "success": True,
        "message": "Section added successfully",
        "data": response
    }

@router.patch("/section/{section_id}", response_model=AddEditSectionResponse)
async def update_form_section(section_id: str, payload: EditSectionPayload, _: GetGuestSession, db: DbSession):

    response = await edit_section_service(section_id, payload, db)

    return {
        "success": True,
        "message": "Section updated successfully",
        "data": response
    }

@router.delete("/section/{section_id}", response_model=APIResponse)
async def delete_form_section(section_id: str, _: GetGuestSession, db: DbSession):

    await delete_section_service(section_id, db)

    return {
        "success": True,
        "message": "Section deleted successfully",
    }

@router.post("/field", response_model=AddEditFieldResponse)
async def add_form_field(payload: AddFieldPayload, session: GetGuestSession, db: DbSession):

    response = await add_field_service(payload, session, db)
    
    return {
        "success": True,
        "message": "field added successfully",
        "data": response 
    }

@router.patch("/field/{field_id}", response_model=AddEditFieldResponse)
async def update_form_field(field_id: str, payload: EditFieldPayload, _: GetGuestSession, db: DbSession):

    response = await edit_field_service(field_id, payload, db)
        
    return {
        "success": True,
        "message": "field updated successfully",
        "data": response 
    }

@router.delete("/field/{field_id}", response_model=APIResponse)
async def delete_form_field(field_id: str, _: GetGuestSession, db: DbSession):

    await delete_section_service(field_id, db)
    
    return {
        "success": True,
        "message": "field deleted successfully",
    }