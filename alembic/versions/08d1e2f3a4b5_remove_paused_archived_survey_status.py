"""remove PAUSED and ARCHIVED survey statuses

Revision ID: 08d1e2f3a4b5
Revises: 07c8d9e0f1a2
Create Date: 2026-06-03 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "08d1e2f3a4b5"
down_revision: Union[str, Sequence[str], None] = "07c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE surveys SET status = 'DRAFT' WHERE status IN ('PAUSED', 'ARCHIVED')")
    op.execute("ALTER TYPE surveystatus RENAME TO surveystatus_old")
    op.execute("CREATE TYPE surveystatus AS ENUM ('DRAFT', 'ACTIVE')")
    op.execute("ALTER TABLE surveys ALTER COLUMN status DROP DEFAULT")
    op.execute(
        "ALTER TABLE surveys ALTER COLUMN status TYPE surveystatus "
        "USING status::text::surveystatus"
    )
    op.execute("ALTER TABLE surveys ALTER COLUMN status SET DEFAULT 'DRAFT'::surveystatus")
    op.execute("DROP TYPE surveystatus_old")


def downgrade() -> None:
    op.execute("ALTER TYPE surveystatus RENAME TO surveystatus_old")
    op.execute("CREATE TYPE surveystatus AS ENUM ('DRAFT', 'ACTIVE', 'PAUSED', 'ARCHIVED')")
    op.execute("ALTER TABLE surveys ALTER COLUMN status DROP DEFAULT")
    op.execute(
        "ALTER TABLE surveys ALTER COLUMN status TYPE surveystatus "
        "USING status::text::surveystatus"
    )
    op.execute("ALTER TABLE surveys ALTER COLUMN status SET DEFAULT 'DRAFT'::surveystatus")
    op.execute("DROP TYPE surveystatus_old")
