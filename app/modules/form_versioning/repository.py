from fastapi import status
from fastapi.exceptions import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.form_versioning.models import FormVersions, Submission, SubmissionAnswer, SubmissionStatus
from app.modules.form_versioning.schema import SaveFormPayload, SubmissionPayload
from datetime import datetime, timezone
from app.modules.forms.models import Form
from app.modules.forms.schemas import FormResponse
async def get_latest_draft(form_id: str, db: AsyncSession):

    version = await db.execute(
        select(FormVersions)
        .where(FormVersions.form_id == form_id, FormVersions.published_at.is_(None))
        .order_by(FormVersions.version_number.desc())
        .limit(1)
    )

    return version.scalar_one_or_none()

async def get_latest_version(form_id: str, db: AsyncSession):
    version = await db.execute(
        select(FormVersions)
        .where(FormVersions.form_id == form_id)
        .order_by(FormVersions.version_number.desc())
        .limit(1)
    )

    return version.scalar_one_or_none()

async def update_draft_version(form_id: str, payload: SaveFormPayload, db: AsyncSession):

    latest_draft = await get_latest_draft(form_id, db)
    form_content = SaveFormPayload.model_validate(
        payload,
        from_attributes=True
    )

    content = form_content.model_dump(mode="json")

    if latest_draft:
        latest_draft.content = content
    else:
        latest_version = await get_latest_version(form_id, db)
        new_version_number = (latest_version.version_number if latest_version else 0) + 1

        new_version = FormVersions(
            form_id=form_id,
            version_number=new_version_number,
            content=content,
        )

        db.add(new_version)

    await db.commit()

    if latest_draft:
        await db.refresh(latest_draft)
        return latest_draft

    await db.refresh(new_version)
    return new_version

async def get_published_version(version_id: str, db: AsyncSession):

    version = await db.execute(
        select(FormVersions)
        .where(FormVersions.id == version_id)
    )

    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published form not found")

    return version.scalar_one_or_none()


async def store_submission(form_id: str, user_id: str | None, payload: SubmissionPayload, db: AsyncSession):

    if user_id:
        exiting_submission = await db.execute(select(Submission).where(Submission.respondent_id == user_id))
        if exiting_submission:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You have already submitted this form")

    submission = Submission(
        form_id=form_id,
        respondent_id=user_id,
        status=SubmissionStatus.SUBMITTED,
        submitted_at=datetime.now(timezone.utc),
        respondent_metadata=payload.respondent_metadata,
    )

    db.add(submission)
    await db.flush()

    answers = [
        SubmissionAnswer(
            submission_id=submission.id,
            field_id=answer.field_id,
            answer_text=answer.answer_text,
            answer_json=answer.answer_json,
        )
        for answer in payload.answers
    ]

    db.add_all(answers)

    await db.commit()

    return