from fastapi import APIRouter
from app.modules.analytics.schema import FormAnalyticsQueryResponse
from app.db.session import DbSession
from app.core.dependencies import GetCurrentUser
from app.modules.analytics.service import get_submission_analytics_service

router = APIRouter(prefix="/analytics", tags=["Form Analytics"])

@router.get("/{form_id}/submits", response_model=FormAnalyticsQueryResponse)
async def get_submission_analytics(form_id: str, user: GetCurrentUser, db: DbSession, page: int | None = 1, limit: int | None = 10, search: str | None = None):

    query = {
        "page": page,
        "limit": limit,
        "search": search,
    }

    response = await get_submission_analytics_service(form_id, user, query, db)

    return {
        "success": True,
        "message": "Submission analytics fetched successfully",
        "data": response
    }
