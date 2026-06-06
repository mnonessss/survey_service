"""responses sessions answers api keys update links

Revision ID: 06a1b2c3d4e5
Revises: 0556ad436697
Create Date: 2026-06-04 18:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "06a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "0556ad436697"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "survey_links",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column("survey_links", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("survey_links", "token", type_=sa.String(length=128), existing_type=sa.String(length=255))

    op.create_table(
        "response_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("link_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_complete", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["link_id"], ["survey_links.id"]),
        sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["response_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "question_id", name="uq_answers_session_question"),
    )

    op.create_table(
        "external_api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("key_prefix", sa.String(length=16), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash"),
    )


def downgrade() -> None:
    op.drop_table("external_api_keys")
    op.drop_table("answers")
    op.drop_table("response_sessions")
    op.drop_column("survey_links", "expires_at")
    op.drop_column("survey_links", "created_at")
