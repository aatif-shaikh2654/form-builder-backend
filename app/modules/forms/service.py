from app.modules.forms.schemas import (CreateFormPayload, EditFormPayload,
    UpdateQuizSettingsPayload)
from fastapi.exceptions import HTTPException
from sqlalchemy import select
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.schemas import GetGuestResponse
from app.modules.forms.repository import create_form, get_form, get_single_form, get_all_forms_query, get_form_settings, create_quiz_settings, get_quiz_settings
from app.modules.forms.models import FormSettings, FormType

async def create_form_service(payload: CreateFormPayload, session: GetGuestResponse, db: AsyncSession):
    form = await create_form(payload, session, db)

    if form.form_type == FormType.QUIZ:
        await create_quiz_settings(form_id=form.id, db=db)

    return form
    

async def edit_form_service(form_id: str, payload: EditFormPayload, session: GetGuestResponse, db: AsyncSession):

    form = await get_form(id=form_id, session=session, db=db)

    if payload.form_type == FormType.QUIZ and form.form_type != FormType.QUIZ:
        await create_quiz_settings(form_id=form.id, db=db)

    form.title = payload.title or form.title
    form.description = payload.description or form.description
    form.form_type = payload.form_type or form.form_type
    form.status = payload.status or form.status


    form_settings = await get_form_settings(form_id=form.id, db=db)

    if form_settings:
        form_settings.confirmation_message = payload.confirmation_message or form_settings.confirmation_message
        form_settings.allow_multiple_submission = (
            payload.allow_multiple_submission
            if payload.allow_multiple_submission is not None
            else form_settings.allow_multiple_submission
        )
        form_settings.require_login = (
            payload.require_login
            if payload.require_login is not None
            else form_settings.require_login
        )
        form_settings.show_progress_bar = (
            payload.show_progress_bar
            if payload.show_progress_bar is not None
            else form_settings.show_progress_bar
        )
        form_settings.shuffle_questions = (
            payload.shuffle_questions
            if payload.shuffle_questions is not None
            else form_settings.shuffle_questions
        )
        form_settings.submission_limit = payload.submission_limit or form_settings.submission_limit
        form_settings.start_at = payload.start_at or form_settings.start_at
        form_settings.end_at = payload.end_at or form_settings.end_at


    await db.commit()
    await db.refresh(form)

    return form

async def get_all_forms_service(query: dict, session: GetGuestResponse, db: AsyncSession):
    return await get_all_forms_query(query, session, db)

async def get_single_form_service(form_id: str, session: GetGuestResponse, db: AsyncSession):
    form = await get_single_form(id=form_id, session=session, db=db)

    return form

async def delete_form_service(form_id: str, session: GetGuestResponse, db: AsyncSession):
    form = await get_form(id=form_id, session=session, db=db)

    await db.delete(form)
    await db.commit()

    return


async def update_quiz_settings_service(form_id: str, payload: UpdateQuizSettingsPayload, session: GetGuestResponse, db: AsyncSession):

    form = await get_form(id=form_id, session=session, db=db)

    quiz_settings = await get_quiz_settings(form_id=form.id, db=db)

    quiz_settings.time_limit = payload.time_limit or quiz_settings.time_limit
    quiz_settings.passing_score = payload.passing_score or quiz_settings.passing_score
    quiz_settings.total_attempts = payload.total_attempts or quiz_settings.total_attempts
    if payload.show_correct_answers is not None:
        quiz_settings.show_correct_answers = payload.show_correct_answers

    if payload.show_score_after_submissions is not None:
        quiz_settings.show_score_after_submissions = payload.show_score_after_submissions

    await db.commit()

    return quiz_settings

