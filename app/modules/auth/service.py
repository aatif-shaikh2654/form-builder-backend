from app.modules.auth.schemas import (AccessTokens, GetGuestResponse, LoginPayload,
    RefreshTokenPayload, RefreshTokenResponse, SignupPayload, UserResponse)
from app.modules.forms.service import get_all_forms_service
from datetime import datetime, timezone, timedelta
from fastapi.exceptions import HTTPException
from fastapi import status
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.repository import create_user, get_user_email, login_attempt, get_user_by_id, create_guest_session
from app.core.config import ENV, JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_SECRET_KEY, JWT_ALGORITHM, JWT_REFRESH_TOKEN_EXPIRE_DAYS
import jwt
from fastapi import Response
from app.modules.auth.models import GuestSession


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

async def sync_session_forms(user_id: str, session_token: str | None, db: AsyncSession):

    session = (await db.execute(select(GuestSession).where(GuestSession.session_token == session_token))).scalar_one_or_none()

    if not session.session_token:
        return

    forms = await get_all_forms_service(
        session={ 
            "session_token": session_token, 
            "user_id": None, 
            "session_id": None }, 
            db=db
        )

    for form in forms:
        form.guest_session_id = None
        form.owner_id = user_id

    await db.commit()
    await db.delete(session)
    await db.flush()

async def signup_user(db: AsyncSession, payload: SignupPayload) -> UserResponse:

    existing_user = await get_user_email(db, payload.email)

    if existing_user:
        raise HTTPException(status_code=status.HTTP_302_FOUND, detail="Email already exists")
    
    password_hash = hash_password(payload.password)

    user = create_user(db, payload, password_hash)

    await sync_session_forms(user_id=user.id, session_token=payload.session_token, db=db)

    return user

async def login_user(db: AsyncSession, payload: LoginPayload) -> AccessTokens:
    user = await get_user_email(db, payload.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email doesn't exist")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    await login_attempt(db, user)
    
    await sync_session_forms(user_id=user.id, session_token=payload.session_token, db=db)

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return { 
        "access_token": access_token, 
        "refresh_token": refresh_token 
    }

def set_token_cookies(response: Response, access_token: str, refresh_token: str):

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )

def delete_cookies(response: Response):
    response.delete_cookie(
            key="access_token",
            path="/",
            httponly=True,
            secure=False,  # True in production with HTTPS
            samesite="lax",
        )
    
    response.delete_cookie(
        key="refresh_token",
        path="/",
        httponly=True,
        secure=False,  # True in production with HTTPS
        samesite="lax",
    )
    

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

async def get_session_service(session: GetGuestResponse, db: AsyncSession):

    session_token = session["session_token"]
    user_id = session["user_id"]
    new_session = None
    if not user_id and not session_token:
        new_session = await create_guest_session(db=db)
        session_token = new_session.session_token
    
    return {
        "session_token": session_token or None,
        "user_id": user_id or None
    }