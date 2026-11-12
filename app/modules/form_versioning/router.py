from fastapi import APIRouter, Form, UploadFile, File
from app.modules.form_versioning.schema import (DraftFormResponse, GetPublishedFormResponse,
    PublishFormResponse, SaveFormPayload, SaveFormResponse, SubmissionPayload)
from app.core.dependencies import GetGuestSession
from app.db.session import DbSession
from app.modules.form_versioning.service import publish_form_service, save_draft_form_service, get_draft_form_service, get_published_form_service, submit_form_service
from app.common.schema import APIResponse
from app.utils.uploads import save_upload_file


router = APIRouter(prefix="/form", tags=["Form versioning"])

@router.put("/{form_id}/save-draft", response_model=SaveFormResponse)
async def save_draft_form(form_id: str, payload: SaveFormPayload, session: GetGuestSession, db: DbSession):

    response = await save_draft_form_service(form_id, payload, session, db)

    return {
        "success": True,
        "message": "Form saved successfully",
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

@router.get("/{form_id}/get-draft", response_model=DraftFormResponse)
async def get_draft_form(form_id: str, session: GetGuestSession, db: DbSession):

    response = await get_draft_form_service(form_id, session, db)

    return {
        "success": True,
        "message": "Latest draft fetched successfully",
        "data": response
    }

@router.get("/{slug}/form", response_model=GetPublishedFormResponse)
async def get_published_form(slug: str, db: DbSession):

    response = await get_published_form_service(slug, db)
    
    return {
        "success": True,
        "message": "Form fetched successfully",
        "data": response
    }

@router.post("/upload")
async def upload_files(files: list[UploadFile]):

    uploaded_files = []

    for file in files:
        metadata = await save_upload_file(file, "temp/uploads/submission")
        uploaded_files.append(metadata)

    return {
        "success": True,
        "message": "Files uploaded successfully",
        "data": uploaded_files
    }

@router.post("/{form_id}/submit", response_model=APIResponse)
async def submit_form(
    form_id: str, 
    payload: SubmissionPayload, 
    db: DbSession
):

    await submit_form_service(form_id, payload, db=db)

    return {
        "success": True,
        "message": "form submitted successfully"
    }