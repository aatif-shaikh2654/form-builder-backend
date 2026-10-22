from fastapi import APIRouter, Depends, status
from app.modules.auth.schemas import (AccessTokens, LoginPayload, LoginResponse, ProfileResponse,
    RefreshTokenPayload, RefreshTokenResponse, SignupPayload, SignupResponse)
from app.db.session import DbSession
from app.modules.auth.service import (login_user, refresh_token_service, set_token_cookies,
    signup_user)
from fastapi import Response
from app.core.dependencies import GetCurrentUser
from app.modules.forms.router import router


router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup", response_model=SignupResponse)
async def signup(payload: SignupPayload, db: DbSession):
    user = await signup_user(db, payload)

    return { 
            "success": True,
            "message": "User signup successfully",
            "data": user
        }

@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginPayload, response: Response, db: DbSession):

    token: AccessTokens = await login_user(db, payload)

    set_token_cookies(response, access_token=token["access_token"], refresh_token=token["refresh_token"])

    return {
        "success": True,
        "message": "User logged successfully",
    }

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(payload: RefreshTokenPayload, response: Response, db: DbSession):

    token: AccessTokens = await refresh_token_service(refresh_token=payload.refresh_token, db=db)

    set_token_cookies(response, access_token=token["access_token"], refresh_token=token["refresh_token"])

    return {
        "success": True,
        "message": "Refresh token updated successfully",
    }

@router.get("/me", response_model=ProfileResponse)
async def get_profile(user: GetCurrentUser, db: DbSession):

    return {
        "success": True,
        "message": "Profile data fetched successfully",
        "data": user
    } 