from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi import status, Depends, Request
from fastapi.exceptions import HTTPException
import jwt
from app.db.session import DbSession
from app.modules.auth.repository import get_user_by_id, get_guest_session
from app.modules.auth.models import User
from app.modules.auth.schemas import GetGuestResponse, UserResponse

async def get_token_user(access_token: str, db: AsyncSession) -> UserResponse:
    payload = jwt.decode(access_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    
    if payload["type"] != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    user_id = payload["sub"]

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    user = await get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return user

async def get_current_user(request: Request, db: DbSession) -> UserResponse:
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not authenticated")

    try: 
        return await get_token_user(access_token, db)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token")

async def get_guest_user(request: Request, db: DbSession) -> GetGuestResponse:
    access_token = request.cookies.get("access_token")
    session_token = request.headers.get("x-session-token")

    try: 
        user = await get_token_user(access_token, db)
        return { "user_id": user.id, "session_id": None, "session_token": None }        
    except Exception:
        session = None
        if session_token:
            session = await get_guest_session(session_token, db)
        
        return { 
            "session_id": session.id if session else None, 
            "session_token": session.session_token if session else None, 
            "user_id": None 
        }
        

GetCurrentUser = Annotated[UserResponse, Depends(get_current_user)]
GetGuestSession = Annotated[GetGuestResponse, Depends(get_guest_user)]