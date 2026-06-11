"""Add session_token to response_sessions for IDOR protection.

Revision ID: 10f1a2b3c4d5
Revises: 09e0f1a2b3c4
Create Date: 2026-06-06 14:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "10f1a2b3c4d5"
down_revision: Union[str, Sequence[str], None] = "09e0f1a2b3c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.add_column(
        "response_sessions",
        sa.Column("session_token", sa.String(length=64), nullable=True),
    )
    op.execute(
        "UPDATE response_sessions SET session_token = encode(gen_random_bytes(32), 'hex') "
        "WHERE session_token IS NULL"
    )
    op.alter_column("response_sessions", "session_token", nullable=False)


def downgrade() -> None:
    op.drop_column("response_sessions", "session_token")
