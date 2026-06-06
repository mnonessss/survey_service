import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("response_sessions.id", ondelete="CASCADE"), nullable=False
    )

    question_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("questions.id"), nullable=False)

    value_text: Mapped[str | None] = mapped_column(Text)

    value_json: Mapped[dict | list | None] = mapped_column(JSONB)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.datetime.now
    )

    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.datetime.now
    )

    session: Mapped["ResponseSession"] = relationship("ResponseSession", back_populates="answers")
