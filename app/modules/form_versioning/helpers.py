
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.modules.forms.models import (
    Form,
    FormSection,
    FormField,
    FieldConditions,
)


def normalize_data(data):
    """Convert Pydantic model or dict into dict."""
    return data if isinstance(data, dict) else data.model_dump()


def get_existing_fields(form):
    """Collect direct and section fields without duplicates."""
    fields = list(form.fields or [])

    for section in form.sections or []:
        fields.extend(section.fields or [])

    return {
        str(field.id): field
        for field in fields
    }


async def upsert_sections(form, payload, existing_sections, db):
    """Create/update sections and return incoming section IDs + fields."""

    incoming_section_ids = set()
    incoming_fields = []

    for section_data in payload.sections or []:
        section_dict = normalize_data(section_data)
        client_section_id = str(section_dict.get("id") or "")

        if client_section_id in existing_sections:
            section = existing_sections[client_section_id]

            section.title = section_dict.get("title", section.title)
            section.description = section_dict.get("description", section.description)
            section.position = section_dict.get("position", section.position)
            section.layout_type = section_dict.get("layout_type", section.layout_type)
            section.column_count = section_dict.get("column_count", section.column_count)
            section.layout_config = section_dict.get("layout_config", section.layout_config)
            section.is_visible = section_dict.get("is_visible", section.is_visible)

        else:
            section = FormSection(
                form_id=form.id,
                title=section_dict.get("title", "New Section"),
                description=section_dict.get("description"),
                position=section_dict.get("position", 0),
                layout_type=section_dict.get("layout_type", "SINGLE_COLUMN"),
                column_count=section_dict.get("column_count", 1),
                layout_config=section_dict.get("layout_config", {}),
                is_visible=section_dict.get("is_visible", True),
            )

            db.add(section)
            await db.flush()

        incoming_section_ids.add(str(section.id))

        for field_data in section_dict.get("fields") or []:
            incoming_fields.append(
                (normalize_data(field_data), section.id)
            )

    return incoming_section_ids, incoming_fields


async def upsert_fields(
    form,
    payload,
    incoming_fields,
    existing_fields,
    db,
):
    """Create/update fields and resolve frontend field IDs."""

    incoming_field_ids = set()
    processed_field_ids = set()
    field_id_map = {}
    incoming_conditions = []

    # Add direct fields
    for field_data in payload.fields or []:
        incoming_fields.append(
            (normalize_data(field_data), None)
        )

    for field_dict, section_id in incoming_fields:
        client_field_id = str(field_dict.get("id") or "")

        if client_field_id and client_field_id in processed_field_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate field ID: {client_field_id}",
            )

        if client_field_id:
            processed_field_ids.add(client_field_id)

        field = existing_fields.get(client_field_id)

        if field:
            # Update existing field
            field.section_id = section_id
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
            # Create new field
            field = FormField(
                form_id=form.id,
                section_id=section_id,
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

        # Map frontend ID and actual database ID
        if client_field_id:
            field_id_map[client_field_id] = field.id

        field_id_map[str(field.id)] = field.id

        # Collect field conditions
        incoming_conditions.append(
            (field, field_dict.get("conditions") or [])
        )

    return incoming_field_ids, field_id_map, incoming_conditions


async def delete_removed_fields(existing_fields, incoming_field_ids, db):
    """Delete fields removed from the payload."""

    for field_id, field in existing_fields.items():
        if field_id not in incoming_field_ids:
            await db.delete(field)


async def delete_removed_sections(existing_sections, incoming_section_ids, db):
    """Delete sections removed from the payload."""

    for section_id, section in existing_sections.items():
        if section_id not in incoming_section_ids:
            await db.delete(section)



async def upsert_field_conditions(
    form,
    incoming_conditions,
    field_id_map,
    db,
):
    """Create/update/delete conditions for incoming source fields."""

    if not incoming_conditions:
        return

    # Get all incoming source field IDs
    incoming_source_ids = {
        str(source_field.id)
        for source_field, _ in incoming_conditions
    }

    # Fetch existing conditions belonging to these source fields
    result = await db.execute(
        select(FieldConditions).where(
            FieldConditions.source_field_id.in_(
                incoming_source_ids
            )
        )
    )

    existing_conditions = result.scalars().all()

    # Group existing conditions by source field
    existing_by_source = {}

    for condition in existing_conditions:
        source_id = str(condition.source_field_id)

        existing_by_source.setdefault(
            source_id, {}
        )[str(condition.id)] = condition

    # Process each source field independently
    for source_field, condition_list in incoming_conditions:

        source_id = str(source_field.id)

        existing_source_conditions = existing_by_source.get(
            source_id, {}
        )

        incoming_condition_ids = set()

        for condition_data in condition_list:

            condition_dict = normalize_data(condition_data)

            # Resolve target field ID
            target_id = str(
                condition_dict.get("target_field_id") or ""
            )

            target_field_id = field_id_map.get(target_id)

            if target_field_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid target field ID: {target_id}",
                )

            # Find existing condition
            condition_id = str(
                condition_dict.get("id") or ""
            )

            condition = existing_source_conditions.get(
                condition_id
            )

            if condition:
                # Update existing condition
                condition.target_field_id = target_field_id
                condition.condition_operator = (
                    condition_dict["condition_operator"]
                )
                condition.condition_value = (
                    condition_dict["condition_value"]
                )
                condition.action = condition_dict["action"]

            else:
                # Create new condition
                condition = FieldConditions(
                    source_field_id=source_field.id,
                    target_field_id=target_field_id,
                    condition_operator=condition_dict[
                        "condition_operator"
                    ],
                    condition_value=condition_dict[
                        "condition_value"
                    ],
                    action=condition_dict["action"],
                )

                db.add(condition)
                await db.flush()

            incoming_condition_ids.add(str(condition.id))

        # Delete conditions removed from this source field
        for condition_id, condition in (
            existing_source_conditions.items()
        ):
            if condition_id not in incoming_condition_ids:
                await db.delete(condition)

    await db.flush()
