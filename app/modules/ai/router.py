from fastapi import APIRouter
from app.modules.ai.schema import GenerateFormPayload
from app.modules.ai.service import generate_form_service
from app.core.dependencies import GetGuestSession
from app.db.session import DbSession
from app.modules.form_versioning.schema import SaveFormResponse

router = APIRouter(prefix="/ai", tags=["AI Form Generator"])

@router.post("/generate-form", response_model=SaveFormResponse)
async def generate_form(payload: GenerateFormPayload, session: GetGuestSession, db: DbSession):

    response = await generate_form_service(
        user_prompt=payload.user_prompt,
        session=session,
        db=db
    )

    return {
        "success": True,
        "message": "Form generated successfully",
        "data": response
    }