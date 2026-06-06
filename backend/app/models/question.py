import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import QuestionType


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    survey_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("surveys.id"), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)

    question_type: Mapped[QuestionType] = mapped_column(Enum(QuestionType), nullable=False)

    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.datetime.now
    )

    survey: Mapped["Survey"] = relationship("Survey", back_populates="questions")

    options: Mapped[list["QuestionOption"]] = relationship(
        "QuestionOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuestionOption.order",
    )


