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

    model_config = ConfigDict(from_attributes=True)

class SignupPayload(BaseModel):
    full_name: str
    email: str
    password: str

class SignupResponse(APIResponse):
    data: UserResponse

class AccessTokens(BaseModel):
    access_token: str
    refresh_token: str

class LoginPayload(BaseModel):
    email: str
    password: str

class LoginResponse(APIResponse):
    pass

class ProfileResponse(APIResponse):
    data: UserResponse

class RefreshTokenPayload(BaseModel):
    refresh_token: str

class RefreshTokenResponse(APIResponse):
    pass

class GetGuestResponse(BaseModel):
    user_id: str | None
    session_id: str | None