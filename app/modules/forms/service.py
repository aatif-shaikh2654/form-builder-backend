from app.modules.forms.schemas import (CreateFormPayload, EditFormPayload, SaveFormPayload,
    SubmissionPayload, UpdateQuizSettingsPayload, UpdateSettingsPayload)
from sqlalchemy import select
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from app.modules.auth.schemas import GetGuestResponse
from app.modules.forms.repository import create_form, get_single_form, get_all_forms_query, get_form_settings, create_quiz_settings, get_quiz_settings, store_submission
from app.modules.auth.models import GuestSession

async def create_form_service(payload: CreateFormPayload, session: GetGuestResponse, db: AsyncSession):
    form = await create_form(payload, session, db)

    if form.form_type == "QUIZ":
        await create_quiz_settings(form_id=form.id, db=db)

    return form
    

async def edit_form_service(form_id: str, payload: EditFormPayload, session: GetGuestResponse, db: AsyncSession):

    form = await get_single_form(id=form_id, session=session, db=db)

    form.title = payload.title or form.title
    form.description = payload.description or form.description
    form.form_type = payload.form_type or form.form_type
    form.status = payload.status or form.status

    await db.commit()
    await db.refresh(form)

    return form

async def get_all_forms_service(query: dict, session: GetGuestResponse, db: AsyncSession):
    return await get_all_forms_query(query, session, db)

async def get_single_form_service(form_id: str, session: GetGuestResponse, db: AsyncSession):
    form = await get_single_form(id=form_id, session=session, db=db)

    return form

async def delete_form_service(form_id: str, session: GetGuestResponse, db: AsyncSession):
    form = await get_single_form(id=form_id, session=session, db=db)

    await db.delete(form)
    await db.commit()

    return

async def update_form_settings_service(form_id: str, payload: UpdateSettingsPayload, session: GetGuestResponse, db: AsyncSession):
    form = await get_single_form(id=form_id, session=session, db=db)
    
    form_settings = await get_form_settings(id=form.form_settings.id, db=db)

    form_settings.confirmation_message = payload.confirmation_message or form_settings.confirmation_message
    form_settings.allow_multiple_submission = payload.allow_multiple_submission or form_settings.allow_multiple_submission
    form_settings.require_login = payload.require_login or form_settings.require_login
    form_settings.show_progress_bar = payload.show_progress_bar or form_settings.show_progress_bar
    form_settings.shuffle_questions = payload.shuffle_questions or form_settings.shuffle_questions
    form_settings.submission_limit = payload.submission_limit or form_settings.submission_limit
    form_settings.start_at = payload.start_at or form_settings.start_at
    form_settings.end_at = payload.end_at or form_settings.end_at

    await db.commit()
    await db.refresh(form_settings)
    
    return form_settings

async def update_quiz_settings_service(form_id: str, payload: UpdateQuizSettingsPayload, session: GetGuestResponse, db: AsyncSession):

    form = await get_single_form(id=form_id, session=session, db=db)

    quiz_settings = await get_quiz_settings(id=form.quiz_settings.id, db=db)

    quiz_settings.time_limit = payload.time_limit or quiz_settings.time_limit
    quiz_settings.passing_score = payload.passing_score or quiz_settings.passing_score
    quiz_settings.total_attempts = payload.total_attempts or quiz_settings.total_attempts
    quiz_settings.show_correct_answers  = payload.show_correct_answers or quiz_settings.show_correct_answers 
    quiz_settings.show_score_after_submissions = payload.show_score_after_submissions or quiz_settings.show_score_after_submissions

    await db.commit()
    await db.refresh(quiz_settings)

    return quiz_settings

async def publish_form_service(form_id: str, session: GetGuestResponse, db: AsyncSession):

    form = await get_single_form(id=form_id, session=session, db=db)

    form.slug = form.title.lower().replace(" ", "-")
    form.status = "PUBLISHED"
    form.published_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(form)

    return form

async def save_draft_form_service(form_id: str, payload: SaveFormPayload, session: GetGuestResponse, db: AsyncSession):

    form = await get_single_form(id=form_id, session=session, db=db)

    form.title = payload.title or form.title
    form.description = payload.description or form.description

    from app.modules.forms.models import FormSection, FormField

    incoming_sections = payload.sections or []
    existing_sections = {str(s.id): s for s in (form.sections or [])}
    existing_fields = {
        str(field.id): field 
        for field in (list(form.fields or []) + [
            field
            for sec in (form.sections or [])
            for field in (sec.fields or [])
        ])
    }

    incoming_section_ids = set()
    incoming_field_ids = set()

    section_id_map = {}
    incoming_fields = []

    # create / update sections 
    for sec_data in incoming_sections:
        sec_dict = (sec_data if isinstance(sec_data, dict) else sec_data.model_dump())

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

            if client_sec_id:
                section_id_map[client_sec_id] = section.id

        actual_sec_id = str(section.id)
        incoming_section_ids.add(actual_sec_id)


        for field_data in (sec_data.get("fields") or []):
            field_dict = (field_data if isinstance(field_data, dict) else field_data.model_dump())

            incoming_fields.append((field_dict, section.id))

    # create / update fields
    for field_data in (payload.fields or []):
        field_dict = (field_data if isinstance(field_data, dict) else field_data.model_dump())
        
        incoming_fields.append((field_dict, None))

    for field_dict, resolved_section_id in incoming_fields:
        client_field_id = str(field_dict.get("id") or "")

        if client_field_id in existing_fields:
            field = existing_fields[client_field_id]

            field.section_id = resolved_section_id
            field.label = field_dict.get("label", field.label)
            field.description = field_dict.get("description", field.description)
            field.field_type = field_dict.get("field_type", field.field_type)
            field.placeholder = field_dict.get("placeholder", field.placeholder)
            field.is_required = field_dict.get("is_required", field.is_required)
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
                values=field_dict.get("fields", []),
                is_required=field_dict.get("is_required", False),
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

    await db.flush()

    # delete removed sections
    for section_id, section in existing_sections.items():
        if section_id not in incoming_section_ids:
            await db.delete(section)

    await db.commit()

    return await get_single_form(id=form_id, session=session, db=db)

async def submit_form_service(form_id: str, payload: SubmissionPayload, session: GuestSession, db: AsyncSession):

    await store_submission(form_id=form_id, user_id=(session["user_id"] or None), payload=payload, db=db)
    
    return