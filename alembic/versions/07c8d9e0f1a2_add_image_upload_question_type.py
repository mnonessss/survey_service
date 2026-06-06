"""add IMAGE_UPLOAD question type

Revision ID: 07c8d9e0f1a2
Revises: 06a1b2c3d4e5
Create Date: 2026-06-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "07c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = "06a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE questiontype ADD VALUE IF NOT EXISTS 'IMAGE_UPLOAD'")


def downgrade() -> None:
    pass
