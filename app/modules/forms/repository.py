from app.modules.forms.schema import CreateFormPayload
from datetime import datetime, timezone
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.forms.models import (FieldConditions, Form, FormField, FormSection, FormSettings,
    FormStatus, QuizSettings)
from app.modules.auth.schema import GetGuestResponse
from fastapi.exceptions import HTTPException
from fastapi import status
from uuid import UUID

async def create_form(payload: CreateFormPayload, session: GetGuestResponse, db: AsyncSession) :

    form = Form(
        owner_id=session["user_id"], 
        guest_session_id=session["session_id"],
        title=payload.title,
        description=payload.description or None,
        form_type=payload.form_type or "FORM",
        form_settings=FormSettings()
    )
    db.add(form)
    await db.commit()
    await db.flush()
    return form


async def get_form(id: str, session: GetGuestResponse, db: AsyncSession):

    form = await db.execute(select(Form).where(
        Form.id == id,
        or_(Form.owner_id == session["user_id"], Form.guest_session_id == session["session_id"])
    ))

    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")

    return form.scalar_one_or_none()

async def get_all_forms(session: GetGuestResponse, db: AsyncSession):
    result = await db.execute(
        select(Form).where(
            or_(
                Form.owner_id == session["user_id"], 
                Form.guest_session_id == session["session_id"]
            )
        )
    )
    return result.scalars().all()

async def get_all_forms_query(query: dict, session: GetGuestResponse, db: AsyncSession):

    page = query.get("page", 1)
    limit = query.get("limit", 10)
    search = query.get("search", "")
    form_type = query.get("form_type", "FORM")

    form_owner = or_(
                Form.owner_id == session["user_id"], 
                Form.guest_session_id == session["session_id"]
            )
    filters = [form_owner]

    if search:
        filters.append(Form.title.ilike(f"%{search}%"))

    if form_type:
        filters.append(Form.form_type == form_type)

    db_query = select(func.count()).select_from(Form)
    count_query = db_query.where(*filters)
    total = await db.scalar(count_query)

    total_forms = await db.scalar(db_query.where(form_owner))
    published_count = await db.scalar(db_query.where(form_owner, Form.status == FormStatus.PUBLISHED))
    draft_count = await db.scalar(db_query.where(form_owner, Form.status == FormStatus.DRAFT))
    quizes_count = await db.scalar(db_query.where(form_owner, Form.quiz_settings is not None))

    result = await db.execute(
        select(Form)
        .where(*filters)
        .order_by(Form.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )

    forms = result.scalars().all() 

    stats = {
        "total_forms": total_forms,
        "published": published_count,
        "drafts": draft_count,
        "quizes": quizes_count
    }

    return {
        "items": forms,
        "stats": stats,
        "total": total or 0,
        "page": page,
        "limit" : limit,
        "total_pages": (total + limit - 1) // limit if total else 0
    }


async def get_single_form(id: str, session: GetGuestResponse, db: AsyncSession):
    result = await db.execute(
        select(Form).options(
            selectinload(Form.form_settings),
            selectinload(Form.quiz_settings),
            selectinload(Form.sections)
            .selectinload(FormSection.fields)
            .selectinload(FormField.conditions_as_source)
            .selectinload(FieldConditions.target_field)
            .selectinload(FormField.conditions_as_source),
            selectinload(Form.fields)
            .selectinload(FormField.conditions_as_source)
            .selectinload(FieldConditions.target_field)
            .selectinload(FormField.conditions_as_source)
        ).where(
            Form.id == id,
            or_(Form.owner_id == session["user_id"], Form.guest_session_id == session["session_id"])
        ).execution_options(populate_existing=True))

    form = result.scalar_one_or_none()

    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")

    return form

async def get_form_settings(form_id: str, db: AsyncSession):
    result = await db.execute(select(FormSettings).where(FormSettings.form_id == form_id))

    return result.scalar_one_or_none()
    

async def create_quiz_settings(form_id: str, db: AsyncSession):

    quiz_settings = (await db.execute(select(QuizSettings).where(QuizSettings.form_id == form_id))).scalar_one_or_none()

    if not quiz_settings:
        quiz_settings = QuizSettings(form_id=form_id)

        db.add(quiz_settings)
        await db.commit()
        await db.refresh(quiz_settings)

    return quiz_settings

async def get_quiz_settings(form_id: str, db: AsyncSession):
    quiz_settings = await db.execute(select(QuizSettings).where(QuizSettings.form_id == form_id))

    return quiz_settings.scalar_one_or_none()