from app.core.dependencies import GetGuestSession
from app.modules.forms.repository import get_single_form, get_form
from fastapi import status
from fastapi.exceptions import HTTPException
from sqlalchemy import select
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.forms.models import Form
from app.modules.form_versioning.schema import SaveFormPayload, SubmissionPayload
from app.modules.auth.schemas import GetGuestResponse
from app.modules.form_versioning.repository import get_latest_draft, update_draft_version, get_latest_draft, get_published_version, store_submission

async def save_draft_form_service(form_id: str, payload: SaveFormPayload, session: GetGuestResponse, db: AsyncSession):

    form = await get_single_form(id=form_id, session=session, db=db)

    if payload.title is not None:
        form.title = payload.title

    if payload.description is not None:
        form.description = payload.description

    from app.modules.forms.models import FormSection, FormField

    incoming_sections = payload.sections or []
    existing_sections = {str(s.id): s for s in (form.sections or [])}

    all_existing_fields = list(form.fields or [])
    
    for sec in (form.sections or []):
        all_existing_fields.extend(sec.fields or [])

    existing_fields = {
        str(field.id): field 
        for field in all_existing_fields
    }

    incoming_section_ids = set()
    incoming_field_ids = set()
    processed_field_ids = set()

    incoming_fields = []

    # create / update sections 
    for sec_data in incoming_sections:
        sec_dict = sec_data if isinstance(sec_data, dict) else sec_data.model_dump()

        client_sec_id = str(sec_dict.get("id") or "")

        if client_sec_id in existing_sections:
            section = existing_sections[client_sec_id]

            section.title = sec_dict.get("title", section.title)
            section.description = sec_dict.get("description", section.description)
            section.position = sec_dict.get("position", section.position)
            section.layout_type = sec_dict.get("layout_type", section.layout_type)
            section.column_count = sec_dict.get("column_count", section.column_count)
            section.layout_config = sec_dict.get("layout_config", section.layout_config)
            section.is_visible = sec_dict.get("is_visible", section.is_visible)

        else:
            section = FormSection(
                form_id=form.id,
                title=sec_dict.get("title", "New Section"),
                description=sec_dict.get("description"),
                position=sec_dict.get("position", 0),
                layout_type=sec_dict.get("layout_type", "SINGLE_COLUMN"),
                column_count=sec_dict.get("column_count", 1),
                layout_config=sec_dict.get("layout_config", {}),
                is_visible=sec_dict.get("is_visible", True),
            )
            db.add(section)
            await db.flush()

        actual_sec_id = str(section.id)
        incoming_section_ids.add(actual_sec_id)


        for field_data in (sec_dict.get("fields") or []):
            field_dict = (field_data if isinstance(field_data, dict) else field_data.model_dump())

            incoming_fields.append((field_dict, section.id))

    # create / update fields
    for field_data in (payload.fields or []):
        field_dict = (field_data if isinstance(field_data, dict) else field_data.model_dump())
        
        incoming_fields.append((field_dict, None))

    for field_dict, resolved_section_id in incoming_fields:
        client_field_id = str(field_dict.get("id") or "")

        if client_field_id and client_field_id in processed_field_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate field ID: {client_field_id}",
            )

        if client_field_id:
            processed_field_ids.add(client_field_id)

        if client_field_id in existing_fields:
            field = existing_fields[client_field_id]

            field.section_id = resolved_section_id
            field.label = field_dict.get("label", field.label)
            field.description = field_dict.get("description", field.description)
            field.field_type = field_dict.get("field_type", field.field_type)
            field.placeholder = field_dict.get("placeholder", field.placeholder)
            field.is_required = field_dict.get("is_required", field.is_required)
            field.is_multiple = field_dict.get("is_multiple", field.is_multiple)
            field.values = field_dict.get("values", field.values)
            field.position = field_dict.get("position", field.position)
            field.validation_rules = field_dict.get("validation_rules", field.validation_rules)
            field.default_values = field_dict.get("default_values", field.default_values)
            field.settings = field_dict.get("settings", field.settings)
        else:
            field = FormField(
                form_id=form.id,
                section_id=resolved_section_id,
                label=field_dict.get("label", "Untitled Question"),
                description=field_dict.get("description"),
                field_type=field_dict.get("field_type", "SHORT_TEXT"),
                placeholder=field_dict.get("placeholder"),
                values=field_dict.get("values", []),
                is_required=field_dict.get("is_required", False),
                is_multiple=field_dict.get("is_multiple", False),
                position=field_dict.get("position", 0),
                validation_rules=field_dict.get("validation_rules", {}),
                default_values=field_dict.get("default_values", {}),
                settings=field_dict.get("settings", {}),
            )

            db.add(field)
            await db.flush()

        incoming_field_ids.add(str(field.id))

    # delete removed fields
    for field_id, field in existing_fields.items():
        if field_id not in incoming_field_ids:
            await db.delete(field)

    # delete removed sections
    for section_id, section in existing_sections.items():
        if section_id not in incoming_section_ids:
            await db.delete(section)

    await db.flush()

    version = await update_draft_version(form_id=form_id, payload=form, db=db)
    form.draft_version = version.version_number or 0

    await db.commit()

    return await get_single_form(id=form_id, session=session, db=db)

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

    draft_form = await get_latest_draft(form_id=form.id, db=db)
    
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