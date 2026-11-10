"""cascade deletes for field foreign keys

Revision ID: dbb2bee0b613
Revises: 4134d23d3a26
Create Date: 2026-11-10 12:41:13.695925

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dbb2bee0b613'
down_revision: Union[str, Sequence[str], None] = '4134d23d3a26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (table, constraint name, local column, referred table)
FOREIGN_KEYS = [
    ("field_answer_keys", "field_answer_keys_field_id_fkey", "field_id", "fields"),
    ("field_conditions", "field_conditions_source_field_id_fkey", "source_field_id", "fields"),
    ("field_conditions", "field_conditions_target_field_id_fkey", "target_field_id", "fields"),
    ("field_scoring", "field_scoring_field_id_fkey", "field_id", "fields"),
    ("fields", "fields_section_id_fkey", "section_id", "sections"),
    ("submission_answers", "submission_answers_field_id_fkey", "field_id", "fields"),
]


def upgrade() -> None:
    """Upgrade schema."""
    for table, name, column, referred in FOREIGN_KEYS:
        op.drop_constraint(name, table, type_="foreignkey")
        op.create_foreign_key(name, table, referred, [column], ["id"], ondelete="CASCADE")


def downgrade() -> None:
    """Downgrade schema."""
    for table, name, column, referred in FOREIGN_KEYS:
        op.drop_constraint(name, table, type_="foreignkey")
        op.create_foreign_key(name, table, referred, [column], ["id"])
