from app.modules.auth.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.analytics.repository import get_submissions


async def get_submission_analytics_service(form_id: str, user: User, query: dict, db: AsyncSession):

    session = { "user_id": user.id, "session_id": None }

    submissions = await get_submissions(form_id, session, query, db)

    return submissions