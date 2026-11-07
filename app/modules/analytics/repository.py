from app.modules.forms.repository import get_form
from sqlalchemy import select, func, or_, cast, String
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import GetGuestSession
from app.modules.form_versioning.models import Submission, SubmissionAnswer


async def get_submissions(form_id: str, session: GetGuestSession, query: dict, db: AsyncSession):

    form = await get_form(form_id, session, db)

    page = query.get("page", 1)
    limit = query.get("limit", 10)
    search = query.get("search", "")

    filters = [Submission.form_id == form.id]

    if search:
        filters.append(Submission.submission_answers.any(
            or_(
                SubmissionAnswer.answer_text.ilike(f"%{search}%"),
                cast(SubmissionAnswer.answer_json, String).ilike(f"%{search}%")
            )
        ))


    submissions = await db.execute(
        select(Submission)
        .options(
            selectinload(Submission.submission_answers)
            .selectinload(SubmissionAnswer.field)
        )
        .where(*filters)
        .order_by(Submission.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit))

    db_query = select(func.count()).select_from(Submission)
    count_query = db_query.where(*filters)
    total = await db.scalar(count_query)

    return {
        "items": submissions.scalars().all(),
        "total": total or 0,
        "page": page,
        "limit" : limit,
        "total_pages": (total + limit - 1) // limit if total else 0
    }