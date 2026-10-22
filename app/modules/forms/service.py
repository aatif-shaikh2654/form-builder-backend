from app.modules.forms.schemas import (AddFieldPayload, AddSectionPayload, CreateFormPayload,
    EditFieldPayload, EditFormPayload, EditSectionPayload, UpdateQuizSettingsPayload,
    UpdateSettingsPayload)
from fastapi.exceptions import HTTPException
from sqlalchemy import select
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models import User
from app.modules.forms.models import Form
from app.modules.auth.schemas import GetGuestResponse
from app.modules.forms.repository import create_form, get_single_form, get_all_forms, get_form_settings, create_quiz_settings, get_quiz_settings, add_section, get_section, add_field, get_field

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

async def get_all_forms_service(session: GetGuestResponse, db: AsyncSession):
    return await get_all_forms(session, db)

async def get_single_form_service(form_id: str, session: GetGuestResponse, db: AsyncSession):
    form = await get_single_form(id=form_id, session=session, db=db)

    return form

async def delete_form_service(form_id: str, session: GetGuestResponse, db: AsyncSession):
    form = await get_single_form(id=form_id, session=session, db=db)

    db.delete(form)
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
    quiz_settings.show_correct_answers  = payload.show_correct_answers  or quiz_settings.show_correct_answers 
    quiz_settings.show_score_after_submissions = payload.show_score_after_submissions or quiz_settings.show_score_after_submissions

    await db.commit()
    await db.refresh(quiz_settings)

    return quiz_settings

async def add_section_service(form_id: str, payload: AddSectionPayload, session: GetGuestResponse, db: AsyncSession):

    form = await get_single_form(id=form_id, session=session, db=db)

    section = await add_section(form_id=form.id, payload=payload, db=db)

    return section

async def edit_section_service(section_id: str, payload: EditSectionPayload, db: AsyncSession):

    section = await get_section(section_id, db)

    section.title = payload.title or section.title
    section.description = payload.description or section.description
    section.position = payload.position or section.position

    await db.commit()
    await db.refresh(section)

    return section

async def delete_section_service(section_id: str, db: AsyncSession):

    section = await get_section(section_id, db)

    db.delete(section)
    await db.commit()

    return

async def add_field_service(form_id: str, payload: AddFieldPayload, session: GetGuestResponse, db: AsyncSession):

    form = await get_single_form(id=form_id, session=session, db=db)

    field = await add_field(form_id=form.id, payload=payload, db=db)

    return field

async def edit_field_service(field_id: str, payload: EditFieldPayload, db: AsyncSession):
    
    field = await get_field(field_id, db)

    if payload.form and payload.section_id:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Form and section id both are not acceptable add either one only")

    field.form_id = payload.form_id or None
    field.section_id = payload.section_id or None

    field.label = payload.label or field.label
    field.description = payload.description or field.description
    field.field_type = payload.field_type or field.field_type
    field.placeholder = payload.placeholder or field.placeholder
    field.is_required = payload.is_required or field.is_required
    field.position = payload.position or field.position
    field.validation_rules = payload.validation_rules or field.validation_rules
    field.default_values = payload.default_values or field.default_values
    field.settings = payload.settings or field.settings

    await db.commit()
    await db.refresh(field)

    return field

async def delete_field_service(field_id: str, db: AsyncSession):

    field = await get_field(field_id, db)

    db.delete(field)
    await db.commit()

    return
