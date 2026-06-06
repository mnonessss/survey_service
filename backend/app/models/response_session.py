import datetime
import secrets
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ResponseSession(Base):
    __tablename__ = "response_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    survey_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("surveys.id"), nullable=False)

    link_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("survey_links.id"), nullable=False)

    session_token: Mapped[str] = mapped_column(String(64), nullable=False)

    is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.datetime.now
    )

    completed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))

    answers: Mapped[list["Answer"]] = relationship(
        "Answer", back_populates="session", cascade="all, delete-orphan"
    )
