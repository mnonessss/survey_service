import datetime
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SurveyLinks(Base):
    __tablename__ = "survey_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    survey_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("surveys.id"), nullable=False)

    token: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.datetime.now
    )

    expires_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))

