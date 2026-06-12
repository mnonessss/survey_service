"""add IMAGE_UPLOAD_MULTIPLE question type

Revision ID: 11b2c3d4e5f6
Revises: 10f1a2b3c4d5
Create Date: 2026-06-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "11b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "10f1a2b3c4d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE questiontype ADD VALUE IF NOT EXISTS 'IMAGE_UPLOAD_MULTIPLE'")


def downgrade() -> None:
    pass
