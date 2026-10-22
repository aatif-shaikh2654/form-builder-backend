from app.modules.auth.schemas import (AccessTokens, LoginPayload, RefreshTokenPayload,
    RefreshTokenResponse, SignupPayload, UserResponse)
from datetime import datetime, timezone, timedelta
from fastapi.exceptions import HTTPException
from fastapi import status
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.repository import create_user, get_user_email, login_attempt, get_user_by_id
from app.core.config import ENV, JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_SECRET_KEY, JWT_ALGORITHM, JWT_REFRESH_TOKEN_EXPIRE_DAYS
import jwt
from fastapi import Response


password_hash = PasswordHash.recommended()

def hash_password(password: str):
    return password_hash.hash(password)

def verify_password(plain_pass: str, hash_pass: str):
    try:
        return password_hash.verify(plain_pass, hash_pass)
    except:
        return False

def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": now + + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.now(timezone.utc)
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(minutes=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


async def signup_user(db: AsyncSession, payload: SignupPayload) -> UserResponse:

    existing_user = await get_user_email(db, payload.email)

    if existing_user:
        raise HTTPException(status_code=status.HTTP_302_FOUND, detail="Email already exists")
    
    password_hash = hash_password(payload.password)

    user = create_user(db, payload, password_hash)

    return user

async def login_user(db: AsyncSession, payload: LoginPayload) -> AccessTokens:
    user = await get_user_email(db, payload.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email doesn't exist")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    await login_attempt(db, user)
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return { 
        "access_token": access_token, 
        "refresh_token": refresh_token 
    }

def set_token_cookies(response: Response, access_token: str, refresh_token: str):

    response.set_cookie(
        key= "access_token",
        value= access_token,
        httponly=True,
        secure=False if ENV == "dev" else True,
        samesite="Lax",
        max_age=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    response.set_cookie(
        key= "refres_token",
        value= refresh_token,
        httponly=True,
        secure=False if ENV == "dev" else True,
        samesite="Lax",
        max_age=JWT_REFRESH_TOKEN_EXPIRE_DAYS * 60
    )
    
    return


async def refresh_token_service(refresh_token: str, db: AsyncSession) -> RefreshTokenResponse:

    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refresh token not found")

    payload = jwt.decode(refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

    if payload["type"] != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = payload["sub"]

    if not user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid refresh token")

    user = await get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    new_refresh_token = create_refresh_token(user_id=user.id)
    new_access_token = create_access_token(user_id=user.id)
    
    return { 
        "access_token": new_refresh_token, 
        "refresh_token": new_access_token 
    }