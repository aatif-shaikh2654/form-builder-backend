from app.core.dependencies import GetGuestSession
from app.modules.forms.repository import get_single_form, get_form
from fastapi import status
from fastapi.exceptions import HTTPException
from sqlalchemy import select
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.forms.models import Form
from app.modules.form_versioning.schema import SaveFormPayload, SubmissionPayload
from app.modules.auth.schema import GetGuestResponse
from app.modules.form_versioning.repository import get_latest_draft, update_draft_version, get_latest_draft, get_published_version, store_submission, get_latest_version
from app.modules.form_versioning.helpers import get_existing_fields, upsert_sections, upsert_field_conditions, upsert_fields, delete_removed_fields, delete_removed_sections

async def save_draft_form_service(form_id: str, payload: SaveFormPayload, session: GetGuestResponse, db: AsyncSession):

    # 1. Get form
    form = await get_single_form(id=form_id, session=session, db=db)

    # 2. Update basic form properties
    if payload.title is not None:
        form.title = payload.title

    if payload.description is not None:
        form.description = payload.description

    # 3. Prepare existing records
    existing_sections = {
        str(section.id): section
        for section in (form.sections or [])
    }

    existing_fields = get_existing_fields(form)

    # 4. Create/update sections
    incoming_section_ids, incoming_fields = await upsert_sections(
        form=form,
        payload=payload,
        existing_sections=existing_sections,
        db=db
    )

    # 5. Create/update fields
    incoming_field_ids, field_id_map, incoming_conditions = await upsert_fields(
        form=form,
        payload=payload,
        incoming_fields=incoming_fields,
        existing_fields=existing_fields,
        db=db,
    )

    # 6. Create/Update conditions
    await upsert_field_conditions(
        form=form,
        incoming_conditions=incoming_conditions,
        field_id_map=field_id_map,
        db=db,
    )

    # 7. Delete removed fields
    await delete_removed_fields(
        existing_fields=existing_fields,
        incoming_field_ids=incoming_field_ids,
        db=db
    )

    # 8. Delete removed sections
    await delete_removed_sections(
        existing_sections=existing_sections,
        incoming_section_ids=incoming_section_ids,
        db=db,
    )

    await db.flush()

    # 10. Reload updated form relationships
    form = await get_single_form(
        id=form_id,
        session=session,
        db=db,
    )

    # 11. Update draft snapshot
    version = await update_draft_version(
        form_id=form_id,
        form=form,
        db=db,
    )

    form.draft_version = version.version_number

    # 12. Commit everything together
    await db.commit()

    return form

async def publish_form_service(form_id: str, session: GetGuestSession, db: AsyncSession):

    form = await get_form(id=form_id, session=session, db=db)
    
    slug = form.title.lower().replace(" ", "-")
    existing_slug = (await db.execute(select(Form).where(Form.slug == slug, Form.id != form_id))).scalar_one_or_none()
    if existing_slug:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Slug already exists, update the form title")

    now = datetime.now(timezone.utc)
    form.slug = slug
    form.status = "PUBLISHED"
    form.published_at = now

    latest_version = await get_latest_draft(form_id, db)

    form.current_published_version_id = latest_version.id
    form.published_version = latest_version.version_number or 0
    latest_version.published_at = now

    await db.commit()
    await db.refresh(form)

    return form

async def get_draft_form_service(form_id: str, session: GetGuestSession, db: AsyncSession):

    form = await get_single_form(form_id, session, db)

    draft_form = await get_latest_version(form_id=form.id, db=db)
    
    return draft_form

async def get_published_form_service(slug: str, db: AsyncSession):

    form = (await db.execute(
        select(Form)
        .where(Form.slug == slug)
    )).scalar_one_or_none()

    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")

    published_version = await get_published_version(version_id=form.current_published_version_id, db=db)

    return published_version


async def submit_form_service(form_id: str, payload: SubmissionPayload, db: AsyncSession):

    await store_submission(form_id=form_id, user_id=None, payload=payload, db=db)

    return