
from sqlalchemy.inspection import inspect
from fastapi.encoders import jsonable_encoder


def serialize_model(instance):
    return {
        column.key: getattr(instance, column.key)
        for column in inspect(instance).mapper.column_attrs
    }

def serialize_field(field):
    conditions = field.__dict__.get("conditions_as_source", [])

    return {
        **serialize_model(field),
        "conditions": [
            {
                "id": str(condition.id),
                "target_field_id": str(condition.target_field_id),
                "source_field_id": str(condition.source_field_id),
                "condition_operator": condition.condition_operator.value,
                "condition_value": condition.condition_value,
                "action": condition.action.value,
                "target_field": {
                    "id": str(condition.target_field.id),
                    "label": condition.target_field.label,
                    "field_type": condition.target_field.field_type.value,
                } if condition.target_field else None,
            }
            for condition in conditions
        ],
    }

def serialize_form_snapshot(form):
    data = serialize_model(form)

    data["form_settings"] = (
        serialize_model(form.form_settings)
        if form.form_settings else None
    )

    data["quiz_settings"] = (
        serialize_model(form.quiz_settings)
        if form.quiz_settings else None
    )

    data["sections"] = [
        {
            **serialize_model(section),
            "fields": [
                serialize_field(field)
                for field in section.fields
            ],
        }
        for section in form.sections
    ]

    data["fields"] = [
        serialize_field(field)
        for field in form.fields
        if field.section_id is None
    ]

    return data