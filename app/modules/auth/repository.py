from app.modules.auth.models import GuestSession, User
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_email(db: AsyncSession, email: str):
    user = await db.execute(select(User).where(User.email == email))
    return user.scalar_one_or_none()

async def get_user_by_id(db: AsyncSession, user_id: str):
    user = await db.execute(select(User).where(User.id == user_id))
    return user.scalar_one_or_none()

async def create_user(db: AsyncSession, user_data, hash_password: str):
    user = User(
        full_name=user_data.full_name,
        email = user_data.email,
        password_hash = hash_password
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user

async def login_attempt(db: AsyncSession, user: User):
    user.last_login_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(user)

    return

async def get_guest_session(session_token: str, db: AsyncSession) -> GuestSession:
    guest_session = await db.execute(
        select(GuestSession).where(
            GuestSession.session_token == session_token, 
            GuestSession.expires_at > datetime.now(timezone.utc)
        )
    ) 

    return guest_session.scalar_one_or_none()


async def create_guest_session(db):
    guest_session = GuestSession(expires_at=datetime.now(timezone.utc) + timedelta(days=30))
    
    db.add(guest_session)
    await db.commit()
    await db.refresh(guest_session)

    return guest_session