from app.db.database import Base
from enum import Enum
from sqlalchemy import String, ForeignKey, Enum as SQLAlchemyEnum, DateTime, Boolean, Integer, CheckConstraint, Numeric, ARRAY
from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy.dialects.postgresql import JSONB, UUID
from datetime import datetime, timezone
from decimal import Decimal

class FormType(Enum):
    FORM = "FORM"
    QUIZ = "QUIZ"
    SURVEY = "SURVEY"
    FEEDBACK = "FEEDBACK"
    POLL = "POLL"

class FormStatus(Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"

class Form(Base):
    __tablename__ = "forms"

    owner_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    guest_session_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("guest_sessions.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    form_type: Mapped[FormType] = mapped_column(SQLAlchemyEnum(FormType, name="form_type"), nullable=False, default=FormType.FORM)
    status: Mapped[FormStatus] = mapped_column(SQLAlchemyEnum(FormStatus, name="form_status"), nullable=False, default=FormStatus.DRAFT)
    slug: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    current_published_version_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey(
            "form_versions.id",
            name="fk_forms_current_published_version_id",
            ondelete="SET NULL",
            use_alter=True,
        ), 
        nullable=True
    )

    published_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    draft_version: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Owners of the form
    user = relationship("User", back_populates="forms", foreign_keys=[owner_id])
    guest_session = relationship("GuestSession", back_populates="forms", foreign_keys=[guest_session_id])

    # Form contents
    form_settings = relationship("FormSettings", back_populates="form", uselist=False, foreign_keys="FormSettings.form_id", cascade="all, delete-orphan", passive_deletes=True)
    sections = relationship("FormSection", back_populates="form", foreign_keys="FormSection.form_id", cascade="all, delete-orphan", passive_deletes=True)
    fields = relationship("FormField", back_populates="form", foreign_keys="FormField.form_id", cascade="all, delete-orphan", passive_deletes=True)
    quiz_settings = relationship("QuizSettings", back_populates="form", foreign_keys="QuizSettings.form_id", uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    form_collaborators = relationship("FormCollaborator", back_populates="form", foreign_keys="FormCollaborator.form_id", cascade="all, delete-orphan", passive_deletes=True)
    form_share_links = relationship("FormShareLink", back_populates="form", foreign_keys="FormShareLink.form_id", cascade="all, delete-orphan", passive_deletes=True)

    # Form versions
    versions = relationship("FormVersions", back_populates="form", foreign_keys="FormVersions.form_id", cascade="all, delete-orphan", passive_deletes=True)
    current_published_version = relationship("FormVersions", foreign_keys=[current_published_version_id], post_update=True)

    submissions = relationship("Submission", foreign_keys="Submission.form_id", back_populates="form", cascade="all, delete-orphan", passive_deletes=True)

class FormSettings(Base):
    __tablename__ = "form_settings"

    form_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("forms.id", ondelete="CASCADE"), index=True, nullable=False)
    confirmation_message: Mapped[str | None] = mapped_column(String, nullable=True)
    allow_multiple_submission: Mapped[bool] = mapped_column(Boolean, default=False)
    require_login: Mapped[bool] = mapped_column(Boolean, default=False)
    show_progress_bar: Mapped[bool] = mapped_column(Boolean, default=True)
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, default=False)
    submission_limit: Mapped[int | None] = mapped_column(Integer, nullable=True) 
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    form = relationship("Form", foreign_keys=[form_id], back_populates="form_settings")

    __table_args__ = (
        CheckConstraint(
            "submission_limit > 0",
            name="check_submission_limit_positive"
        ),
    )

class LayoutType(Enum):
    GRID = "GRID"
    SINGLE_COLUMN = "SINGLE_COLUMN"
class FormSection(Base):
    __tablename__ = "sections"

    form_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("forms.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    layout_type: Mapped[LayoutType] = mapped_column(SQLAlchemyEnum(LayoutType, name="layout_type"), nullable=False, default=LayoutType.SINGLE_COLUMN)
    column_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    layout_config: Mapped[dict] = mapped_column(JSONB, default={})
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)

    form = relationship("Form", foreign_keys=[form_id], back_populates="sections")
    fields = relationship("FormField", back_populates="section", cascade="all, delete-orphan", passive_deletes=True)

    __table_args__ = (
        CheckConstraint(
            "column_count >= 1 AND column_count <= 12",
            name="check_column_count_range",
        ),
    )

class FieldType(Enum):
    SHORT_TEXT = "SHORT_TEXT"
    LONG_TEXT = "LONG_TEXT"
    SINGLE_CHOICE = "SINGLE_CHOICE"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    DROPDOWN = "DROPDOWN"
    NUMBER = "NUMBER"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    URL = "URL"
    DATE = "DATE"
    TIME = "TIME"
    DATE_TIME = "DATE_TIME"
    RATING = "RATING"
    FILE_UPLOAD = "FILE_UPLOAD"
    CHECKBOX = "CHECKBOX"
    SECTION_HEADING = "SECTION_HEADING"

class FormField(Base):
    __tablename__ = "fields"

    form_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("forms.id", ondelete="CASCADE"), index=True, nullable=True)
    section_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sections.id"), nullable=True)
    label: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    field_type: Mapped[FieldType] = mapped_column(SQLAlchemyEnum(FieldType, name="field_type"), default=FieldType.SHORT_TEXT)
    placeholder: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    is_multiple: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    values: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True, default=list)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    validation_rules: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    default_values: Mapped[dict] = mapped_column(JSONB, nullable=True)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    
    form = relationship("Form", foreign_keys=[form_id], back_populates="fields")
    section = relationship("FormSection", foreign_keys=[section_id], back_populates="fields")
    field_scoring = relationship("FieldScoring", foreign_keys="FieldScoring.field_id", back_populates="fields", cascade="all, delete-orphan", passive_deletes=True)
    field_answer_key = relationship("FieldAnswerKey", foreign_keys="FieldAnswerKey.field_id", back_populates="fields", cascade="all, delete-orphan", passive_deletes=True)
    conditions_as_source = relationship("FieldConditions", foreign_keys="FieldConditions.source_field_id", back_populates="source_field", cascade="all, delete-orphan", passive_deletes=True)
    conditions_as_target = relationship("FieldConditions", foreign_keys="FieldConditions.target_field_id", back_populates="target_field", cascade="all, delete-orphan", passive_deletes=True)
    submission_answers = relationship("SubmissionAnswer", back_populates="field", cascade="all, delete-orphan", passive_deletes=True)

class QuizSettings(Base):
    __tablename__ = "quiz_settings"

    form_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("forms.id", ondelete="CASCADE"), index=True, nullable=False)
    time_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    passing_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"), nullable=False)
    total_attempts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    show_correct_answers : Mapped[bool] = mapped_column(Boolean, default=False)
    show_score_after_submissions: Mapped[bool] = mapped_column(Boolean, default=True)

    form = relationship("Form", foreign_keys=[form_id], back_populates="quiz_settings")

    __table_args__ = (
        CheckConstraint(
            "time_limit IS NULL or time_limit > 0",
            name="check_time_limit_positive"
        ),
        CheckConstraint(
            "passing_score >= 0 AND passing_score <= 100",
            name="check_passing_score_range"
        ),
        CheckConstraint(
            "total_attempts IS NULL or total_attempts > 0",
            name="check_total_attempts_positive"
        ),
    )

class FieldAnswerKey(Base):
    __tablename__ = "field_answer_keys"

    field_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fields.id"), nullable=False)
    correct_answer: Mapped[dict] = mapped_column(JSONB, nullable=False)
    explanation: Mapped[str] = mapped_column(String, nullable=True)

    fields = relationship("FormField", foreign_keys=[field_id], back_populates="field_answer_key")


class FieldScoring(Base):
    __tablename__ = "field_scoring"

    field_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fields.id"), nullable=False)
    points: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=1)
    allow_partial_credit: Mapped[bool] = mapped_column(Boolean, default=False)

    fields = relationship("FormField", foreign_keys=[field_id], back_populates="field_scoring")

    __table_args__ = (
        CheckConstraint(
            "points > 0",
            name="check_points_non_negative"
        ),
    )

class ConditionOperator(Enum):
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    CONTAINS = "CONTAINS"
    NOT_CONTAINS = "NOT_CONTAINS"
    EMPTY = "EMPTY"
    FILLED = "FILLED"

class ConditionActions(Enum):
    SHOW = "SHOW"
    HIDE = "HIDE"

class FieldConditions(Base):
    __tablename__ = "field_conditions"

    source_field_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fields.id"), nullable=False)
    target_field_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fields.id"), nullable=False)
    condition_operator: Mapped[Enum] = mapped_column(SQLAlchemyEnum(ConditionOperator, name="condition_operator"), nullable=False)
    condition_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    action: Mapped[ConditionActions] = mapped_column(SQLAlchemyEnum(ConditionActions, name="action"), nullable=False)

    source_field = relationship("FormField", foreign_keys=[source_field_id], back_populates="conditions_as_source")
    target_field = relationship("FormField", foreign_keys=[target_field_id], back_populates="conditions_as_target")


class CollabRole(Enum):
    VIEWER = "VIEWER"
    EDITOR = "EDITOR"
    OWNER = "OWNER"

class FormCollaborator(Base):
    __tablename__ = "form_collaborators"

    form_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("forms.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    role: Mapped[CollabRole] = mapped_column(SQLAlchemyEnum(CollabRole, name="role"), nullable=False, default=CollabRole.VIEWER)

    user = relationship("User", foreign_keys=[user_id], back_populates="form_collaborators")
    form = relationship("Form", foreign_keys=[form_id], back_populates="form_collaborators")

class FormShareLink(Base):
    __tablename__ = "form_share_links"

    form_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("forms.id", ondelete="CASCADE"), index=True, nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    form = relationship("Form", foreign_keys=[form_id], back_populates="form_share_links")

