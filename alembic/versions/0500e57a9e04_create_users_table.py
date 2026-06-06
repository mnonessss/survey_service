"""create users table

Revision ID: 0500e57a9e04
Revises:
Create Date: 2026-06-01 13:06:54.267174

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0500e57a9e04"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_role_enum = postgresql.ENUM(
    "ADMIN", "RESEARCHER", "VIEWER", name="userrole", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    user_role_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False, server_default="RESEARCHER"),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("external_id"),
    )


def downgrade() -> None:
    op.drop_table("users")
    bind = op.get_bind()
    user_role_enum.drop(bind, checkfirst=True)
