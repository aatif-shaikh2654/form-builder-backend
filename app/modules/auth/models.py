from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import   String, Boolean, Enum as SQLAlchemyEnum, DateTime
from datetime import datetime, timezone
from enum import Enum
import secrets

class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    SUPERADMIN = "SUPERADMIN"

class User(Base):
    __tablename__ = "users"

    #   Don't need to add id it is already in the base 
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLAlchemyEnum(UserRole, name="user_role"), nullable=False, default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=True)

    forms = relationship("Form", back_populates="user", foreign_keys="Form.owner_id", cascade="all, delete-orphan", passive_deletes=True)
    form_collaborators = relationship("FormCollaborator", foreign_keys="FormCollaborator.user_id", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    versions = relationship("FormVersions", foreign_keys="FormVersions.published_by_id", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    submissions = relationship("Submission", back_populates="user", foreign_keys="Submission.respondent_id")

class GuestSession(Base):

    __tablename__ = "guest_sessions"

    session_token: Mapped[str] = mapped_column(String, unique=True, nullable=False, default=lambda: secrets.token_urlsafe(32))
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

    forms = relationship("Form", back_populates="guest_session", foreign_keys="Form.guest_session_id")