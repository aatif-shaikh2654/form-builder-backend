
"""submission model fix

Revision ID: 86a5efaa0428
Revises: e2ca752594a3
Create Date: 2026-10-28 23:48:41.933864
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers
revision: str = "86a5efaa0428"
down_revision: Union[str, Sequence[str], None] = "e2ca752594a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the new nullable respondent_id column
    op.add_column(
        "submissions",
        sa.Column("respondent_id", sa.UUID(), nullable=True),
    )

    # Remove the old response_id foreign key
    op.drop_constraint(
        "submissions_response_id_fkey",
        "submissions",
        type_="foreignkey",
    )

    # Create a named foreign key for respondent_id
    op.create_foreign_key(
        "fk_submissions_respondent_id_users",
        "submissions",
        "users",
        ["respondent_id"],
        ["id"],
    )

    # Remove the old response_id column
    op.drop_column("submissions", "response_id")


def downgrade() -> None:
    # Restore the old column
    op.add_column(
        "submissions",
        sa.Column("response_id", sa.UUID(), nullable=True),
    )

    # Copy data back before removing respondent_id
    op.execute(
        """
        UPDATE submissions
        SET response_id = respondent_id
        WHERE respondent_id IS NOT NULL
        """
    )

    # Remove the new foreign key
    op.drop_constraint(
        "fk_submissions_respondent_id_users",
        "submissions",
        type_="foreignkey",
    )

    # Restore the old foreign key
    op.create_foreign_key(
        "submissions_response_id_fkey",
        "submissions",
        "users",
        ["response_id"],
        ["id"],
    )

    # Remove the new column
    op.drop_column("submissions", "respondent_id")
