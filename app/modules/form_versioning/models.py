from app.db.database import Base
from sqlalchemy import ForeignKey, Integer, DateTime, String, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from enum import Enum


class FormVersions(Base):
    __tablename__ = "form_versions"

    form_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("forms.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False, default={})
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_by_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    form = relationship("Form", back_populates="versions", foreign_keys=[form_id])
    user = relationship("User", back_populates="versions", foreign_keys=[published_by_id])

class SubmissionStatus(Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    ABANDONED = "ABANDONED"

class Submission(Base):
    __tablename__ = "submissions"

    form_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("forms.id", ondelete="CASCADE"), index=True, nullable=False)
    respondent_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    response_number: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[SubmissionStatus] = mapped_column(SQLAlchemyEnum(SubmissionStatus, name="status"), nullable=False, default=SubmissionStatus.IN_PROGRESS)
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=lambda: datetime.now(timezone.utc))
    submitted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    respondent_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default={})

    form = relationship("Form", foreign_keys=[form_id], back_populates="submissions")
    user = relationship("User", foreign_keys=[respondent_id], back_populates="submissions")
    submission_answers = relationship("SubmissionAnswer", foreign_keys="SubmissionAnswer.submission_id", back_populates="submission", cascade="all, delete-orphan", passive_deletes=True)

class SubmissionAnswer(Base):
    __tablename__ = "submission_answers"

    submission_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"), index=True, nullable=False)
    field_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fields.id", ondelete="CASCADE"), nullable=False)
    answer_text: Mapped[str] = mapped_column(String, nullable=True)
    answer_json: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)

    submission = relationship("Submission", foreign_keys=[submission_id], back_populates="submission_answers")
    field = relationship("FormField", foreign_keys=[field_id], back_populates="submission_answers")
