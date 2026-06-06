import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class QuestionOption(Base):
    __tablename__ = "question_options"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )

    label: Mapped[str] = mapped_column(String(255), nullable=False)

    value: Mapped[str] = mapped_column(String(255), nullable=False)

    image_url: Mapped[str | None] = mapped_column(String(255))

    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.datetime.now
    )

    question: Mapped["Question"] = relationship("Question", back_populates="options")

