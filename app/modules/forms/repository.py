from app.modules.forms.schemas import (AddFieldPayload, AddSectionPayload, CreateFormPayload,
    UpdateSettingsPayload)
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.forms.models import Form, FormField, FormSection, FormSettings, QuizSettings
from app.modules.auth.schemas import GetGuestResponse
from fastapi.exceptions import HTTPException
from fastapi import status

async def create_form(payload: CreateFormPayload, session: GetGuestResponse, db: AsyncSession) :

    form = Form(
        owner_id=session["user_id"], 
        guest_session_id=session["session_id"],
        title=payload.title,
        description=payload.description,
        form_type=payload.form_type,
        form_settings=FormSettings()
    )
    db.add(form)
    await db.commit()
    await db.refresh(form)
    return form

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

async def get_single_form(id: str, session: GetGuestResponse, db: AsyncSession):
    result = await db.execute(
        select(Form).options(
            selectinload(Form.form_settings),
            selectinload(Form.quiz_settings),
            selectinload(Form.sections).selectinload(Form.fields),
            selectinload(Form.fields)
        ).where(
            Form.id == id,
            or_(Form.owner_id == session["user_id"], Form.guest_session_id == session["session_id"])
        ))

    if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")

    return result.scalar_one_or_none()

async def get_form_settings(id: str, db: AsyncSession):
    result = await db.execute(select(FormSettings).where(FormSettings.id == id))

    return result.scalar_one_or_none()
    

async def create_quiz_settings(form_id: str, db: AsyncSession):
    quiz_settings = QuizSettings(form_id=form_id)

    await db.commit()
    await db.refresh(quiz_settings)

    return quiz_settings

async def get_quiz_settings(id: str, db: AsyncSession):
    quiz_settings = await db.execute(select(QuizSettings).where(QuizSettings.id == id))

    return quiz_settings.scalar_one_or_none()

async def add_section(form_id: str, payload: AddSectionPayload, db: AsyncSession):

    section = FormSection(
                form_id=form_id,
                title=payload.title,
                description=payload.description,
                position=payload.position,
                )

    db.add(section)
    await db.commit()
    await db.refresh(section)

    return section

async def get_section(section_id: str, db: AsyncSession):
    section = await db.execute(select(FormSection).where(FormSection.id == section_id))

    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

    return section.scalar_one_or_none()

async def add_field(form_id: str, payload: AddFieldPayload, db: AsyncSession):

    field = FormField(
        form_id=form_id,
        section_id=payload.section_id,
        label=payload.label,
        description=payload.description,
        field_type=payload.field_type,
        placeholder=payload.placeholder,
        is_required=payload.is_required,
        position=payload.position,
        validation_rules=payload.validation_rules,
        default_values=payload.default_values,
        settings=payload.settings,
    )

    db.add(field)
    await db.commit()
    await db.refresh(field)

    return field

async def get_field(field_id: str, db: AsyncSession):
    field = await db.execute(select(FormField).where(FormField.id == field_id))

    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")

    return field.scalar_one_or_none()