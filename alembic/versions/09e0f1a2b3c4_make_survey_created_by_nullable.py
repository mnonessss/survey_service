"""Make surveys.created_by optional after removing user authentication.

Revision ID: 09e0f1a2b3c4
Revises: 08d1e2f3a4b5
Create Date: 2026-06-06 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "09e0f1a2b3c4"
down_revision: Union[str, Sequence[str], None] = "08d1e2f3a4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("surveys", "created_by", existing_type=sa.UUID(), nullable=True)


def downgrade() -> None:
    op.alter_column("surveys", "created_by", existing_type=sa.UUID(), nullable=False)
