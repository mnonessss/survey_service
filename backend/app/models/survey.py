import uuid
import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SurveyStatus


class Survey(Base):
    __tablename__ = "surveys"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    title: Mapped[str] = mapped_column(String(255), nullable=False)

    description: Mapped[str | None] = mapped_column(Text)

    status: Mapped[SurveyStatus] = mapped_column(Enum(SurveyStatus), nullable=False, default=SurveyStatus.DRAFT)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID, ForeignKey("users.id"), nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.datetime.now)

    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.datetime.now)

    questions: Mapped[list["Question"]] = relationship(
        "Question",
        back_populates="survey",
        cascade="all, delete-orphan",
        order_by="Question.order",
    )

