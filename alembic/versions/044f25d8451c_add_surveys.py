"""add surveys

Revision ID: 044f25d8451c
Revises: 0500e57a9e04
Create Date: 2026-06-03 18:05:22.523311

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "044f25d8451c"
down_revision: Union[str, Sequence[str], None] = "0500e57a9e04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

survey_status_enum = postgresql.ENUM(
    "DRAFT", "ACTIVE", "PAUSED", "ARCHIVED", name="surveystatus", create_type=False
)
question_type_enum = postgresql.ENUM(
    "SINGLE_CHOICE",
    "MULTIPLE_CHOICE",
    "TEXT",
    "IMAGE_CHOICE",
    "RATING",
    "DATE",
    name="questiontype",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    survey_status_enum.create(bind, checkfirst=True)
    question_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "surveys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", survey_status_enum, nullable=False, server_default="DRAFT"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("question_type", question_type_enum, nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "question_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.Column("image_url", sa.String(length=255), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "survey_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )


def downgrade() -> None:
    op.drop_table("survey_links")
    op.drop_table("question_options")
    op.drop_table("questions")
    op.drop_table("surveys")

    bind = op.get_bind()
    question_type_enum.drop(bind, checkfirst=True)
    survey_status_enum.drop(bind, checkfirst=True)
