from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from app.modules.ai.schema import AIFormSchema
from app.modules.ai.prompts import SYSTEM_PROMPT
from app.modules.auth.models import GuestSession
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.forms.models import (
    Form,
    FormSettings,
    FormSection,
    FormField,
    QuizSettings,
    FieldScoring,
    FieldAnswerKey,
    FieldConditions,
)
from sqlalchemy import select
from app.modules.forms.schema import FormType, FormStatus
from app.modules.forms.service import get_single_form
from app.modules.form_versioning.service import update_draft_version

# Langchain integration
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    max_tokens=8192
)

structured_llm = llm.with_structured_output(AIFormSchema)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{user_prompt}")
])


form_generation_chain = prompt | structured_llm


# API services
async def generate_form_service(
    user_prompt: str,
    session: GuestSession,
    db: AsyncSession,
):
    # 1. Generate form
    result: AIFormSchema = await form_generation_chain.ainvoke({
        "user_prompt": user_prompt
    })

    # 2. Create form settings
    form_settings = FormSettings(
        **result.form_settings.model_dump()
    )

    # 3. Create form
    form = Form(
        owner_id=session["user_id"],
        guest_session_id=session["session_id"],
        title=result.title,
        description=result.description,
        form_type=result.form_type,
        status=FormStatus.DRAFT,
        form_settings=form_settings,
    )

    db.add(form)
    await db.flush()

    # 4. Create quiz settings
    if result.form_type == FormType.QUIZ:
        quiz_settings = QuizSettings(
            form_id=form.id,
            **result.quiz_settings.model_dump(),
        )

        db.add(quiz_settings)

    # 5. Create sections
    section_map = {}

    for section_data in result.sections:
        section = FormSection(
            form_id=form.id,
            title=section_data.title,
            description=section_data.description,
            position=section_data.position,
            layout_type=section_data.layout_type,
            column_count=section_data.column_count,
            layout_config=section_data.layout_config,
            is_visible=section_data.is_visible,
        )

        db.add(section)
        await db.flush()

        section_map[section_data.id] = section

    # 6. Create fields
    field_map = {}

    all_fields = []

    # Section fields
    for section_data in result.sections:
        for field_data in section_data.fields:
            all_fields.append((field_data, section_map[section_data.id]))

    # Root fields
    for field_data in result.fields:
        all_fields.append((field_data, None))

    for field_data, section in all_fields:
        field = FormField(
            form_id=form.id,
            section_id=section.id if section else None,
            label=field_data.label,
            description=field_data.description,
            field_type=field_data.field_type,
            placeholder=field_data.placeholder,
            is_required=field_data.is_required,
            is_multiple=field_data.is_multiple,
            values=field_data.values,
            position=field_data.position,
            validation_rules=field_data.validation_rules,
            default_values=field_data.default_values,
            settings=field_data.settings,
        )

        db.add(field)
        await db.flush()

        field_map[field_data.field_key] = field

        # Quiz scoring
        if result.form_type == FormType.QUIZ:

            if field_data.field_scoring:
                db.add(
                    FieldScoring(
                        field_id=field.id,
                        points=field_data.field_scoring.points,
                        allow_partial_credit=(
                            field_data.field_scoring.allow_partial_credit
                        ),
                    )
                )

            if field_data.field_answer_key:
                db.add(
                    FieldAnswerKey(
                        field_id=field.id,
                        correct_answer=(
                            field_data.field_answer_key.correct_answer
                        ),
                        explanation=(
                            field_data.field_answer_key.explanation
                        ),
                    )
                )

    # 7. Create field conditions
    for field_data, section in all_fields:

        for condition in field_data.conditions:

            source_field = field_map.get(condition.source_field_key)
            target_field = field_map.get(condition.target_field_key)

            if not source_field or not target_field:
                continue

            db.add(
                FieldConditions(
                    source_field_id=source_field.id,
                    target_field_id=target_field.id,
                    condition_operator=condition.condition_operator,
                    condition_value=condition.condition_value,
                    action=condition.action,
                )
            )

    # 8. Reload form with relationships
    await db.flush()

    form_id = str(form.id)

    form = await get_single_form(
        id=form_id,
        session=session,
        db=db
    )

    version = await update_draft_version(
        form_id=form.id,
        form=form,
        db=db,
    )

    form.draft_version = version.version_number

    # 9. Commit
    await db.commit()

    # Reload form with relationships AFTER commit
    form = await get_single_form(
        id=form_id,
        session=session,
        db=db
    )

    return form