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

    forms = relationship("Form", back_populates="user")
    form_collaborators = relationship("FormCollaborator", back_populates="user")

class GuestSession(Base):

    __tablename__ = "guest_sessions"

    session_token: Mapped[str] = mapped_column(String, unique=True, nullable=False, default=lambda: secrets.token_urlsafe(32))
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

    forms = relationship("Form", back_populates="guest_session")