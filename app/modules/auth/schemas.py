from pydantic import BaseModel, ConfigDict
from uuid import UUID
from app.modules.auth.models import UserRole
from datetime import datetime
from app.common.schema import APIResponse, ModelType


class UserResponse(ModelType):
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    is_email_verified: bool
    last_login_at: datetime

class SignupPayload(BaseModel):
    full_name: str
    email: str
    password: str
    session_token: str | None

class SignupResponse(APIResponse):
    data: UserResponse

class AccessTokens(BaseModel):
    access_token: str
    refresh_token: str

class LoginPayload(BaseModel):
    email: str
    password: str
    session_token: str | None

class LoginResponse(APIResponse):
    pass

class ProfileResponse(APIResponse):
    data: UserResponse

class RefreshTokenPayload(BaseModel):
    refresh_token: str

class RefreshTokenResponse(APIResponse):
    pass

class GuestUser(BaseModel):
    user_id: UUID | None
    session_token: str | None
class GetGuestResponse(GuestUser):
    session_id: UUID | None

class GetGuestSessionResponse(APIResponse):
    data: GuestUser
